import json
import asyncio
import hashlib
import secrets
import time
import re
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs

try:
    import curl_cffi
    from curl_cffi.requests import AsyncSession
    has_curl_cffi = True
except ImportError:
    has_curl_cffi = False

try:
    import zendriver as nodriver
    has_nodriver = True
except ImportError:
    has_nodriver = False

from .base import BaseProvider

logger = logging.getLogger("flashy.lmarena")

Lmarena_IMAGE_CACHE: Dict[str, dict] = {}


def uuid7():
    timestamp_ms = int(time.time() * 1000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    uuid_int = timestamp_ms << 80
    uuid_int |= (0x7000 | rand_a) << 64
    uuid_int |= (0x8000000000000000 | rand_b)
    hex_str = f"{uuid_int:032x}"
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def check_link_expiry(url: str) -> bool:
    try:
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        amz_date_str = params.get("X-Amz-Date", [None])[0]
        expires_delta = params.get("X-Amz-Expires", [None])[0]
        if not amz_date_str or not expires_delta:
            return False
        creation_time = datetime.strptime(amz_date_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        expiry_time = creation_time.timestamp() + int(expires_delta)
        current_time = datetime.now(timezone.utc).timestamp()
        return current_time <= expiry_time
    except Exception:
        return False


def get_cache_dir() -> Path:
    cache_dir = Path.home() / ".cache" / "flashy" / "lmarena"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


Lmarena_ACTIONS = {
    "generateUploadUrl": "7012303914af71fce235a732cde90253f7e2986f2b",
    "getSignedUrl": "605373b76a30947cc26be49fc7b00c885910e21559",
    "updateTouConsent": "40efff1040868c07750a939a0d8120025f246dfe28",
    "createPointwiseFeedback": "605a0e3881424854b913fe1d76d222e50731b6037b",
    "createPairwiseFeedback": "600777eb84863d7e79d85d214130d3214fc744c80f",
    "getProxyImage": "60049198d4936e6b7acc63719b63b89284c58683e6",
    "deleteEvaluationSession": "6009c985d7e84eae2ec94547453ba388005b22e2a5",
    "getEmailProvider": "607c2dd3d84af5a00b322b577498d1b2a739c5dfe0",
    "deleteAccount": "40a57e8c369eaf8a82483fae2f8106489ce041dffd",
}

Lmarena_TEXT_MODELS: Dict[str, str] = {}
Lmarena_IMAGE_MODELS: Dict[str, str] = {}
Lmarena_VIDEO_MODELS: Dict[str, str] = {}
Lmarena_VISION_MODELS: List[str] = []
Lmarena_ALL_MODELS: List[Dict[str, Any]] = []
Lmarena_MODELS_LOADED = False
Lmarena_MODELS_LAST_FETCH = 0
LMARENA_MODELS_CACHE_TTL = 3600

BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://arena.ai",
    "referer": "https://arena.ai/",
    "sec-ch-ua": '"Google Chrome";v="136", "Chromium";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}


class LmarenaProvider(BaseProvider):
    URL = "https://arena.ai"
    CREATE_EVALUATION_URL = "https://arena.ai/nextjs-api/stream/create-evaluation"
    POST_TO_EVALUATION_URL = "https://arena.ai/nextjs-api/stream/post-to-evaluation/{id}"
    MODELS_URL = "https://arena.ai/?mode=direct"
    
    _auth_cache: Dict[str, Any] = {}
    
    @classmethod
    def _get_auth_cache_path(cls) -> Path:
        return get_cache_dir() / "auth_cache.json"
    
    @classmethod
    def _get_models_cache_path(cls) -> Path:
        return get_cache_dir() / "models_cache.json"
    
    @classmethod
    def load_auth_cache(cls) -> Dict[str, Any]:
        cache_path = cls._get_auth_cache_path()
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load auth cache: {e}")
        return {}
    
    @classmethod
    def save_auth_cache(cls, auth_data: Dict[str, Any]):
        cache_path = cls._get_auth_cache_path()
        try:
            with open(cache_path, "w") as f:
                json.dump(auth_data, f)
        except Exception as e:
            logger.warning(f"Failed to save auth cache: {e}")
    
    @classmethod
    def load_models_cache(cls) -> bool:
        cache_path = cls._get_models_cache_path()
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    data = json.load(f)
                global Lmarena_TEXT_MODELS, Lmarena_IMAGE_MODELS, Lmarena_VIDEO_MODELS, Lmarena_VISION_MODELS, Lmarena_ALL_MODELS, Lmarena_MODELS_LOADED, Lmarena_MODELS_LAST_FETCH
                Lmarena_TEXT_MODELS = data.get("text_models", {})
                Lmarena_IMAGE_MODELS = data.get("image_models", {})
                Lmarena_VIDEO_MODELS = data.get("video_models", {})
                Lmarena_VISION_MODELS = data.get("vision_models", [])
                Lmarena_ALL_MODELS = data.get("models", [])
                Lmarena_MODELS_LAST_FETCH = data.get("last_fetch", 0)
                Lmarena_MODELS_LOADED = True
                logger.info(f"Loaded {len(Lmarena_ALL_MODELS)} models from cache")
                return True
            except Exception as e:
                logger.warning(f"Failed to load models cache: {e}")
        return False
    
    @classmethod
    def save_models_cache(cls):
        cache_path = cls._get_models_cache_path()
        try:
            with open(cache_path, "w") as f:
                json.dump({
                    "text_models": Lmarena_TEXT_MODELS,
                    "image_models": Lmarena_IMAGE_MODELS,
                    "video_models": Lmarena_VIDEO_MODELS,
                    "vision_models": Lmarena_VISION_MODELS,
                    "models": Lmarena_ALL_MODELS,
                    "last_fetch": Lmarena_MODELS_LAST_FETCH,
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save models cache: {e}")
    
    @classmethod
    def parse_models_from_html(cls, html: str) -> bool:
        global Lmarena_TEXT_MODELS, Lmarena_IMAGE_MODELS, Lmarena_VIDEO_MODELS, Lmarena_VISION_MODELS, Lmarena_ALL_MODELS, Lmarena_MODELS_LOADED, Lmarena_MODELS_LAST_FETCH
        
        try:
            idx = html.find('initialModels')
            if idx < 0:
                logger.error("initialModels not found in HTML")
                return False
            
            colon_idx = html.find(':', idx)
            if colon_idx < 0:
                logger.error("Colon not found after initialModels")
                return False
            
            bracket_idx = html.find('[', colon_idx)
            if bracket_idx < 0:
                logger.error("Opening bracket not found")
                return False
            
            depth = 0
            end = bracket_idx
            for i in range(bracket_idx, min(bracket_idx + 500000, len(html))):
                if html[i] == '[':
                    depth += 1
                elif html[i] == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            
            models_json = html[bracket_idx:end]
            models_json = models_json.encode().decode('unicode_escape')
            models = json.loads(models_json)
            
            text_models = {}
            image_models = {}
            video_models = {}
            vision_models = []
            all_models = []
            
            for model in models:
                public_name = model.get("publicName", "")
                model_id = model.get("id", "")
                capabilities = model.get("capabilities", {})
                output_caps = capabilities.get("outputCapabilities", {})
                input_caps = capabilities.get("inputCapabilities", {})
                
                # output_caps is a dict like {"text": true, "image": true}
                if output_caps.get("text"):
                    text_models[public_name] = model_id
                if output_caps.get("image"):
                    image_models[public_name] = model_id
                if output_caps.get("video"):
                    video_models[public_name] = model_id
                if input_caps.get("image"):
                    vision_models.append(public_name)
                
                all_models.append({
                    "id": public_name,
                    "name": model.get("displayName", public_name),
                    "capabilities": {
                        "chat": True,
                        "stream": True,
                        "vision": "image" in input_caps,
                        "reasoning": False,
                        "tools": False,
                    }
                })
            
            Lmarena_TEXT_MODELS = text_models
            Lmarena_IMAGE_MODELS = image_models
            Lmarena_VIDEO_MODELS = video_models
            Lmarena_VISION_MODELS = vision_models
            Lmarena_ALL_MODELS = all_models
            Lmarena_MODELS_LOADED = True
            Lmarena_MODELS_LAST_FETCH = time.time()
            
            cls.save_models_cache()
            logger.info(f"Parsed {len(all_models)} models from HTML")
            return True
        except Exception as e:
            logger.error(f"Failed to parse models from HTML: {e}")
            import traceback
            traceback.print_exc()
        return False
    
    @classmethod
    def parse_actions_from_js(cls, js_text: str):
        global Lmarena_ACTIONS
        try:
            pattern = r'\("([a-f0-9]{40,})".*?"(\w+)"\)'
            matches = re.findall(pattern, js_text)
            for v, k in matches:
                if len(v) >= 40:
                    Lmarena_ACTIONS[k] = v
                    logger.debug(f"Found action: {k} = {v}")
        except Exception as e:
            logger.warning(f"Failed to parse actions from JS: {e}")
    
    @classmethod
    async def fetch_models(cls, proxy: str = None) -> List[Dict[str, Any]]:
        if Lmarena_MODELS_LOADED and (time.time() - Lmarena_MODELS_LAST_FETCH) < LMARENA_MODELS_CACHE_TTL:
            return Lmarena_ALL_MODELS
        
        if cls.load_models_cache():
            if (time.time() - Lmarena_MODELS_LAST_FETCH) < LMARENA_MODELS_CACHE_TTL:
                return Lmarena_ALL_MODELS
        
        try:
            headers = BROWSER_HEADERS.copy()
            async with AsyncSession(impersonate="chrome", headers=headers, proxy=proxy, timeout=30) as session:
                resp = await session.get(cls.MODELS_URL)
                if resp.status_code == 200:
                    html = resp.text
                    cls.parse_models_from_html(html)
                    
                    js_url_match = re.search(r'src="(/_next/static/chunks/main-app-[^"]+\.js)"', html)
                    if js_url_match:
                        js_url = f"https://arena.ai{js_url_match.group(1)}"
                        js_resp = await session.get(js_url)
                        if js_resp.status_code == 200:
                            cls.parse_actions_from_js(js_resp.text)
                    
                    if Lmarena_MODELS_LOADED:
                        return Lmarena_ALL_MODELS
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
        
        if Lmarena_MODELS_LOADED:
            return Lmarena_ALL_MODELS
        
        return []
    
    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        """Fetch available models for this provider (called by router)."""
        await cls.fetch_models()
        return Lmarena_ALL_MODELS

    async def make_request_via_browser(
        self,
        data: dict,
        proxy: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not has_nodriver:
            yield {"error": "zendriver is required. Install with: pip install zendriver"}
            return
        
        profile_dir = Path.home() / ".cache" / "flashy" / "lmarena_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Using browser profile: {profile_dir}")
        
        browser_args = [
            "--window-size=1280,720",
            "--disable-gpu",
        ]
        
        browser = None
        page = None
        
        try:
            logger.info("Starting browser...")
            browser = await nodriver.start(
                headless=False,
                browser_args=browser_args,
                user_data_dir=str(profile_dir),
            )
            
            if not browser:
                logger.error("Failed to start browser - nodriver.start() returned None")
                yield {"error": "Failed to start browser. Make sure Chrome is installed."}
                return
            
            logger.info("Browser started successfully")
            logger.info(f"Browser object: {browser}")
            logger.info(f"Browser tabs: {browser.tabs}")
            
            # Get the initial tab
            tabs = browser.tabs
            if not tabs:
                logger.error("No tabs found after browser start")
                yield {"error": "Browser started but no tabs found"}
                return
            
            page = tabs[0]
            logger.info(f"Initial page: {page}, URL: {page.url if hasattr(page, 'url') else 'N/A'}")
            
            logger.info("Navigating to arena.ai...")
            await page.get("https://arena.ai/?mode=direct")
            logger.info("Page loaded, waiting for content...")
            await asyncio.sleep(5)
            
            logger.info(f"Current page URL after load: {page.url if hasattr(page, 'url') else 'N/A'}")
            
            # Check if already logged in using browser-level cookie access
            try:
                all_cookies = await browser.cookies.get()
                page_cookies = [c for c in all_cookies if 'arena.ai' in (c.domain or '')]
                cookie_names = [c.name for c in page_cookies]
            except Exception as e:
                logger.warning(f"Failed to get cookies: {e}")
                page_cookies = []
                cookie_names = []
            
            valid_auth = False
            for c in page_cookies:
                cname = c.name.lower()
                if ('session' in cname or 'token' in cname or 'clerk' in cname or 'auth' in cname):
                    valid_auth = True
                    break
            
            has_auth = valid_auth
            
            logger.info(f"Initial cookies: {cookie_names}")
            
            if not has_auth:
                logger.info("Waiting for user to log in (120 seconds)...")
                print("\n" + "="*60)
                print(">>> NOT LOGGED IN.")
                print(">>> Please LOG INTO arena.ai in the browser window.")
                print(">>> Window will stay open for 120 seconds.")
                print("="*60 + "\n")
                
                # Simple wait - don't check cookies, just wait
                for i in range(120):
                    await asyncio.sleep(1)
                    if i % 10 == 0:
                        logger.info(f"Waiting for login... {i}s elapsed")
                
                # After waiting, check if login was successful
                try:
                    all_cookies = await browser.cookies.get()
                    page_cookies = [c for c in all_cookies if 'arena.ai' in (c.domain or '')]
                    valid_auth = False
                    for c in page_cookies:
                        cname = c.name.lower()
                        if ('session' in cname or 'token' in cname or 'clerk' in cname or 'auth' in cname):
                            valid_auth = True
                            break
                    has_auth = valid_auth
                except Exception as e:
                    logger.warning(f"Failed to check cookies after wait: {e}")
                    has_auth = False
            
            if not has_auth:
                logger.error("Login timeout")
                yield {"error": "Login timeout. Please try again."}
                return
            
            logger.info("Login detected! Proceeding with API call...")
            await asyncio.sleep(2)
            
            if not has_auth:
                logger.error("Login timeout")
                yield {"error": "Login timeout. Please try again."}
                return
            
            logger.info("User logged in! Navigating to arena.ai to ensure session is active...")
            await browser.get("https://arena.ai/")
            await asyncio.sleep(2)
            
            try:
                url = await page.evaluate("window.location.href")
                logger.info(f"Current page URL: {url}")
            except Exception as e:
                logger.warning(f"Page appears closed: {e}")
                yield {"error": "Browser window was closed. Please try again."}
                return
            
            logger.info("Waiting for ReCAPTCHA...")
            for i in range(30):
                try:
                    is_ready = await page.evaluate('typeof window.grecaptcha !== "undefined" && typeof window.grecaptcha.enterprise !== "undefined"')
                    if is_ready:
                        logger.info("ReCAPTCHA ready")
                        break
                except Exception as e:
                    logger.warning(f"Error checking ReCAPTCHA: {e}")
                await asyncio.sleep(0.5)
            
            logger.info("Getting ReCAPTCHA token...")
            captcha = await page.evaluate(
                """new Promise((resolve) => {
                    if (!window.grecaptcha || !window.grecaptcha.enterprise) {
                        resolve("");
                        return;
                    }
                    window.grecaptcha.enterprise.ready(async () => {
                        try {
                            const token = await window.grecaptcha.enterprise.execute(
                                '6Led_uYrAAAAAKjxDIF58fgFtX3t8loNAK85bW9I',
                                { action: 'chat_submit' }
                            );
                            resolve(token);
                        } catch (e) {
                            resolve("");
                        }
                    });
                });""",
                await_promise=True
            )
            
            if not captcha:
                logger.error("Failed to get ReCAPTCHA token")
                yield {"error": "Failed to get ReCAPTCHA token"}
                return
            
            logger.info(f"Got ReCAPTCHA token (len={len(captcha)})")
            
            data["recaptchaV3Token"] = captcha
            
            logger.info(f"Making API call with model: {data.get('modelAId', 'unknown')}")
            
            logger.info("Checking cookies before API call...")
            debug_cookies = await page.evaluate("""
                document.cookie
            """)
            logger.info(f"Document cookies: {debug_cookies[:200] if debug_cookies else 'none'}")
            
            ls_keys = await page.evaluate("Object.keys(localStorage)")
            logger.info(f"LocalStorage keys: {ls_keys}")
            
            # Let's try to find an auth token if it exists (e.g. clerk)
            auth_token = await page.evaluate("""
                (() => {
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        if (key.includes('clerk') || key.includes('token') || key.includes('auth')) {
                            return localStorage.getItem(key);
                        }
                    }
                    return null;
                })()
            """)
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
                'Origin': 'https://arena.ai',
                'Referer': 'https://arena.ai/'
            }
            
            # We will use window.fetch to trigger any interceptors, or just pass cookies manually if needed
            result = await page.evaluate(
                f"""(async () => {{
                    try {{
                        const response = await window.fetch('/nextjs-api/stream/create-evaluation', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Accept': 'text/event-stream'
                            }},
                            credentials: 'same-origin',
                            body: JSON.stringify({json.dumps(data)})
                        }});
                        
                        if (!response.ok) {{
                            const text = await response.text();
                            return 'ERROR:' + response.status + ':' + text;
                        }}
                        
                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        let result = '';
                        
                        while (true) {{
                            const {{ done, value }} = await reader.read();
                            if (done) break;
                            result += decoder.decode(value, {{ stream: true }});
                        }}
                        
                        return result;
                    }} catch (err) {{
                        return 'FETCH_ERROR:' + err.toString();
                    }}
                }})()""",
                await_promise=True
            )
            
            logger.info(f"Response length: {len(result) if result else 0}")
            
            if result and result.startswith("ERROR:"):
                parts = result.split(":", 2)
                status = parts[1] if len(parts) > 1 else "?"
                error_text = parts[2] if len(parts) > 2 else ""
                logger.error(f"API error: {status} - {error_text[:200]}")
                yield {"error": f"Error {status}: {error_text[:200]}"}
                return
            
            if result and result.startswith("FETCH_ERROR:"):
                yield {"error": f"Fetch error: {result[12:]}"}
                return
            
            has_content = False
            if result:
                for line in result.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        if line.startswith("a0:"):
                            chunk = json.loads(line[3:])
                            if isinstance(chunk, str) and chunk == "hasArenaError":
                                yield {"error": "Arena error"}
                                return
                            if isinstance(chunk, list):
                                for item in chunk:
                                    if isinstance(item, dict) and "text" in item:
                                        has_content = True
                                        yield {"text": item.get("text", "")}
                        elif line.startswith("ag:"):
                            chunk = json.loads(line[3:])
                            if isinstance(chunk, str):
                                yield {"thought": chunk}
                        elif line.startswith("a2:"):
                            chunk = json.loads(line[3:])
                            if isinstance(chunk, list):
                                images = [item.get("image") for item in chunk if isinstance(item, dict) and item.get("image")]
                                if images:
                                    yield {"images": images}
                        elif line.startswith("ad:"):
                            finish_data = json.loads(line[3:])
                            if "usage" in finish_data:
                                yield {"usage": finish_data["usage"]}
                            yield {"is_final": True}
                            return
                        elif line.startswith("a3:"):
                            error_data = json.loads(line[3:])
                            yield {"error": f"Arena error: {error_data}"}
                            return
                    except json.JSONDecodeError:
                        continue
            
            if not has_content:
                yield {"error": "Empty response"}
            yield {"is_final": True}
        except asyncio.CancelledError:
            logger.warning("Request was cancelled")
            yield {"error": "Request cancelled"}
        except Exception as e:
            logger.exception(f"Browser request failed: {e}")
            yield {"error": f"Browser error: {str(e)}"}
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not has_nodriver:
            yield {"error": "zendriver is required. Install with: pip install zendriver"}
            return
        
        proxy = kwargs.get("proxy")
        
        await self.fetch_models(proxy)
        
        model_name = model or ""
        model_id = None
        
        if model_name in Lmarena_TEXT_MODELS:
            model_id = Lmarena_TEXT_MODELS[model_name]
        elif model_name in Lmarena_IMAGE_MODELS:
            model_id = Lmarena_IMAGE_MODELS[model_name]
        elif model_name in Lmarena_VIDEO_MODELS:
            model_id = Lmarena_VIDEO_MODELS[model_name]
        
        if not model_id and Lmarena_ALL_MODELS:
            for m in Lmarena_ALL_MODELS:
                if m["id"] == model_name:
                    model_id = Lmarena_TEXT_MODELS.get(model_name, model_name)
                    break
        
        if not model_id:
            if Lmarena_ALL_MODELS:
                default_model = Lmarena_ALL_MODELS[0]
                model_name = default_model["id"]
                model_id = Lmarena_TEXT_MODELS.get(model_name, model_name)
            else:
                yield {"error": "No models available"}
                return
        
        prompt = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
                break
        
        if not prompt:
            prompt = messages[-1].get("content", "") if messages else ""
        
        evaluation_session_id = str(uuid7())
        user_message_id = str(uuid7())
        model_a_message_id = str(uuid7())
        is_image_model = model_name in Lmarena_IMAGE_MODELS
        
        data = {
            "id": evaluation_session_id,
            "mode": "direct",
            "userMessageId": user_message_id,
            "modelAMessageId": model_a_message_id,
            "userMessage": {
                "content": prompt,
                "experimental_attachments": [],
                "metadata": {}
            },
            "modality": "image" if is_image_model else "chat",
            "modelAId": model_id,
        }
        
        async for chunk in self.make_request_via_browser(data, proxy):
            yield chunk