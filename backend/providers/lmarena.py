import json
import asyncio
import secrets
import time
import re
import logging
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

try:
    import curl_cffi
    from curl_cffi.requests import AsyncSession
    has_curl_cffi = True
except ImportError:
    has_curl_cffi = False

try:
    import zendriver as nodriver
    from zendriver import cdp
    has_nodriver = True
except ImportError:
    has_nodriver = False

from .base import BaseProvider

logger = logging.getLogger("flashy.lmarena")


def uuid7():
    timestamp_ms = int(time.time() * 1000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    uuid_int = timestamp_ms << 80
    uuid_int |= (0x7000 | rand_a) << 64
    uuid_int |= (0x8000000000000000 | rand_b)
    hex_str = f"{uuid_int:032x}"
    return f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


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

AUTH_COOKIE_NAME = "arena-auth-prod-v1"

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

_global_browser = None
_global_page = None


class LmarenaProvider(BaseProvider):
    URL = "https://arena.ai"
    CREATE_EVALUATION_URL = "https://arena.ai/nextjs-api/stream/create-evaluation"
    POST_TO_EVALUATION_URL = "https://arena.ai/nextjs-api/stream/post-to-evaluation/{id}"
    MODELS_URL = "https://arena.ai/?mode=direct"

    @classmethod
    def _get_models_cache_path(cls) -> Path:
        return get_cache_dir() / "models_cache.json"

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
        await cls.fetch_models()
        return Lmarena_ALL_MODELS

    @classmethod
    async def ensure_browser(cls, proxy: str = None):
        """Ensure browser is open and user is logged in. Returns (browser, page) or raises."""
        global _global_browser, _global_page

        if not has_nodriver:
            raise RuntimeError("zendriver is required")

        if _global_browser is not None and not getattr(_global_browser, 'stopped', True):
            return _global_browser, _global_page

        profile_dir = Path.home() / ".cache" / "flashy" / "lmarena_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting browser...")
        _global_browser = await nodriver.start(
            headless=False,
            browser_args=["--no-sandbox"],
            user_data_dir=str(profile_dir),
        )

        if not _global_browser:
            raise RuntimeError("Failed to start browser")

        tabs = _global_browser.tabs
        if not tabs:
            raise RuntimeError("No tabs found")

        _global_page = tabs[0]
        await _global_page.get("https://arena.ai/?mode=direct")
        await asyncio.sleep(3)

        # Check if already logged in
        has_auth = await _global_page.evaluate(f'document.cookie.indexOf("{AUTH_COOKIE_NAME}") >= 0')

        if not has_auth:
            logger.info("Not logged in, waiting for user...")
            print("\n" + "=" * 60)
            print(">>> NOT LOGGED IN.")
            print(">>> Please LOG INTO arena.ai in the browser window.")
            print("=" * 60 + "\n")

            for i in range(300):
                await asyncio.sleep(1)
                try:
                    has_auth = await _global_page.evaluate(f'document.cookie.indexOf("{AUTH_COOKIE_NAME}") >= 0')
                    if has_auth:
                        logger.info("User logged in!")
                        break
                except Exception:
                    # Page may have navigated during login
                    await asyncio.sleep(2)

            if not has_auth:
                raise RuntimeError("Login timeout. Please try again.")

        return _global_browser, _global_page

    @classmethod
    async def get_grecaptcha_token(cls, page) -> str:
        """Get a fresh ReCAPTCHA token from the browser page.
        
        Strategy: The page loads recaptcha with a specific site key via render= parameter.
        We extract that key and use it with execute(). If that fails server-side,
        we fall back to using the page's own recaptcha widget.
        """
        # Wait for grecaptcha to load
        for i in range(60):
            try:
                ready = await page.evaluate('!!(window.grecaptcha && window.grecaptcha.enterprise && window.grecaptcha.enterprise.execute)')
                if ready:
                    break
            except Exception:
                pass
            await asyncio.sleep(1)
        else:
            logger.error("ReCAPTCHA not available after 60s")
            return ""

        logger.info("ReCAPTCHA enterprise available, extracting site key...")

        # Extract site key from the recaptcha script src (render= parameter)
        site_key = await page.evaluate("""(function() {
            var scripts = document.querySelectorAll('script[src*="recaptcha"]');
            for (var i = 0; i < scripts.length; i++) {
                var m = scripts[i].src.match(/[?&]render=([^&]+)/);
                if (m) return m[1];
            }
            return '';
        })()""")

        if site_key:
            logger.info(f"Found ReCAPTCHA site key from script src: {site_key}")
        else:
            logger.warning("Could not find ReCAPTCHA site key from script src, trying other methods...")
            site_key = await page.evaluate(r"""(function() {
                var allScripts = document.querySelectorAll('script:not([src])');
                for (var i = 0; i < allScripts.length; i++) {
                    var text = allScripts[i].textContent;
                    if (text) {
                        var m = text.match(/grecaptcha\.enterprise\.execute\s*\(\s*['"]([A-Za-z0-9_-]{39,42})['"]/);
                        if (m) return m[1];
                    }
                }
                var el = document.querySelector('[data-sitekey]');
                if (el) return el.getAttribute('data-sitekey');
                return '';
            })()""")

        if not site_key:
            logger.error("Could not find any ReCAPTCHA site key")
            return ""

        logger.info(f"Using ReCAPTCHA site key: {site_key}")

        # Log recaptcha script info for debugging
        recaptcha_info = await page.evaluate("""(function() {
            var scripts = document.querySelectorAll('script[src*="recaptcha"]');
            return Array.from(scripts).map(s => s.src);
        })()""")
        logger.info(f"ReCAPTCHA script sources: {recaptcha_info}")

        # Try direct execute first
        try:
            captcha = await page.evaluate(
                f"""window.grecaptcha.enterprise.execute('{site_key}', {{ action: 'chat_submit' }});""",
                await_promise=True
            )
            if captcha and isinstance(captcha, str) and len(captcha) > 10:
                logger.info(f"Got ReCAPTCHA token via direct execute (len={len(captcha)})")
                return captcha
        except Exception as e:
            logger.warning(f"Direct execute failed: {e}")

        # Fallback: use .ready() wrapper
        try:
            captcha = await page.evaluate(
                f"""new Promise((resolve) => {{
                    window.grecaptcha.enterprise.ready(async () => {{
                        try {{
                            const token = await window.grecaptcha.enterprise.execute(
                                '{site_key}',
                                {{ action: 'chat_submit' }}
                            );
                            resolve(token);
                        }} catch (e) {{
                            resolve("ERROR:" + e.message);
                        }}
                    }});
                }});""",
                await_promise=True
            )
            if captcha and isinstance(captcha, str):
                if captcha.startswith("ERROR:"):
                    logger.error(f"ReCAPTCHA ready() error: {captcha}")
                    return ""
                if len(captcha) > 10:
                    logger.info(f"Got ReCAPTCHA token via ready() wrapper (len={len(captcha)})")
                    return captcha
        except Exception as e:
            logger.error(f"ReCAPTCHA ready() wrapper failed: {e}")

        logger.error("Failed to get ReCAPTCHA token")
        return ""

        logger.info("ReCAPTCHA enterprise available, extracting site key...")

        # Extract site key from the page — check scripts, inline JS, and next data
        site_key = await page.evaluate(r"""(function() {
            // Check recaptcha script src for render parameter
            var scripts = document.querySelectorAll('script[src*="recaptcha"]');
            for (var i = 0; i < scripts.length; i++) {
                var m = scripts[i].src.match(/[?&]render=([^&]+)/);
                if (m) return m[1];
            }
            // Check inline scripts for the key
            var allScripts = document.querySelectorAll('script:not([src])');
            for (var i = 0; i < allScripts.length; i++) {
                var text = allScripts[i].textContent;
                if (text) {
                    var m = text.match(/grecaptcha\.enterprise\.execute\s*\(\s*['"]([A-Za-z0-9_-]{39,42})['"]/);
                    if (m) return m[1];
                    var m2 = text.match(/sitekey['"]*\s*[:=]\s*['"]([A-Za-z0-9_-]{39,42})['"]/i);
                    if (m2) return m2[1];
                    var m3 = text.match(/recaptcha[^]*?['"]([A-Za-z0-9_-]{39,42})['"]/);
                    if (m3) return m3[1];
                }
            }
            // Check data-sitekey attribute
            var el = document.querySelector('[data-sitekey]');
            if (el) return el.getAttribute('data-sitekey');
            return '';
        })()""")

        if not site_key:
            # Also search Next.js data for the recaptcha key
            site_key = await page.evaluate("""(function() {
                // Check __NEXT_DATA__
                if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props && window.__NEXT_DATA__.props.pageProps) {
                    var props = window.__NEXT_DATA__.props.pageProps;
                    if (props.recaptchaSiteKey) return props.recaptchaSiteKey;
                    if (props.RECAPTCHA_SITE_KEY) return props.RECAPTCHA_SITE_KEY;
                }
                // Check window.__env
                if (window.__env && window.__env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY) {
                    return window.__env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;
                }
                // Check all script src for render param
                var scripts = document.querySelectorAll('script[src]');
                for (var i = 0; i < scripts.length; i++) {
                    var m = scripts[i].src.match(/[?&]render=([^&]+)/);
                    if (m) return m[1];
                }
                return '';
            })()""")
        
        if not site_key:
            logger.error("Could not extract ReCAPTCHA site key from page")
            return ""

        logger.info(f"Using ReCAPTCHA site key: {site_key}")

        # Try direct execute first
        try:
            captcha = await page.evaluate(
                f"""window.grecaptcha.enterprise.execute('{site_key}', {{ action: 'chat_submit' }});""",
                await_promise=True
            )
            if captcha and isinstance(captcha, str) and len(captcha) > 10:
                logger.info(f"Got ReCAPTCHA token via direct execute (len={len(captcha)})")
                return captcha
        except Exception as e:
            logger.warning(f"Direct execute failed: {e}")

        # Fallback: use .ready() wrapper
        try:
            captcha = await page.evaluate(
                f"""new Promise((resolve) => {{
                    window.grecaptcha.enterprise.ready(async () => {{
                        try {{
                            const token = await window.grecaptcha.enterprise.execute(
                                '{site_key}',
                                {{ action: 'chat_submit' }}
                            );
                            resolve(token);
                        }} catch (e) {{
                            resolve("ERROR:" + e.message);
                        }}
                    }});
                }});""",
                await_promise=True
            )
            if captcha and isinstance(captcha, str):
                if captcha.startswith("ERROR:"):
                    logger.error(f"ReCAPTCHA ready() error: {captcha}")
                    return ""
                if len(captcha) > 10:
                    logger.info(f"Got ReCAPTCHA token via ready() wrapper (len={len(captcha)})")
                    return captcha
        except Exception as e:
            logger.error(f"ReCAPTCHA ready() wrapper failed: {e}")

        logger.error("Failed to get ReCAPTCHA token")
        return ""

    async def make_request_via_browser(
        self,
        data: dict,
        proxy: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not has_nodriver:
            yield {"type": "error", "error": "zendriver is required. Install with: pip install zendriver"}
            return

        logger.info("make_request_via_browser: starting...")

        try:
            browser, page = await self.ensure_browser(proxy)
            logger.info("make_request_via_browser: browser ready")
        except Exception as e:
            logger.error(f"make_request_via_browser: browser error: {e}")
            yield {"type": "error", "error": f"Browser error: {str(e)}"}
            return

        # Navigate to arena.ai if needed
        try:
            url = await page.evaluate("window.location.href")
            logger.info(f"make_request_via_browser: page at {url}")
            if "arena.ai" not in url:
                logger.info("Navigating back to arena.ai...")
                await page.get("https://arena.ai/?mode=direct")
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Page check failed: {e}")
            yield {"type": "error", "error": f"Browser error: {str(e)}"}
            return

        # Check authentication before making request
        authed = await page.evaluate('document.cookie.indexOf("arena-auth-prod-v1") >= 0')
        if not authed:
            logger.warning("No auth cookie found, refreshing page...")
            await page.get("https://arena.ai/text/direct")
            await asyncio.sleep(5)
            authed = await page.evaluate('document.cookie.indexOf("arena-auth-prod-v1") >= 0')
            if not authed:
                logger.error("Still no auth cookie after refresh")
                yield {"type": "error", "error": "Not logged into arena.ai. Please log in via the browser."}
                return

        # Get ReCAPTCHA token
        logger.info("make_request_via_browser: getting ReCAPTCHA token...")
        captcha = await self.get_grecaptcha_token(page)
        if not captcha:
            logger.error("make_request_via_browser: failed to get ReCAPTCHA token")
            yield {"type": "error", "error": "Failed to get ReCAPTCHA token. Please refresh the browser page and try again."}
            return

        logger.info(f"make_request_via_browser: got ReCAPTCHA token (len={len(captcha)})")
        data["recaptchaV3Token"] = captcha

        logger.info(f"Making API call with model: {data.get('modelAId', 'unknown')}")
        prompt_text = data.get("userMessage", {}).get("content", "")

        # Set up response interceptor to capture the real browser's own requests
        # and also capture what headers the page normally sends
        await page.evaluate("""(function() {
            window.__lastEvalResponse = null;
            window.__lastEvalError = null;
            window.__capturedHeaders = null;
            const origFetch = window.__origFetch || window.fetch;
            window.__origFetch = origFetch;
            window.fetch = async function(...args) {
                const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
                if (url.includes('create-evaluation') || url.includes('post-to-evaluation')) {
                    const headers = args[1]?.headers ? Object.fromEntries(
                        args[1].headers instanceof Headers ? args[1].headers.entries() : Object.entries(args[1].headers)
                    ) : {};
                    window.__capturedHeaders = headers;
                }
                const response = await origFetch.apply(this, args);
                if (url.includes('create-evaluation') || url.includes('post-to-evaluation')) {
                    try {
                        const cloned = response.clone();
                        const reader = cloned.body.getReader();
                        const decoder = new TextDecoder();
                        let body = '';
                        while (true) {
                            const { done, value } = await reader.read();
                            if (done) break;
                            body += decoder.decode(value, { stream: true });
                        }
                        window.__lastEvalResponse = {
                            status: response.status,
                            body: body,
                            url: url
                        };
                    } catch(e) {
                        window.__lastEvalError = e.toString();
                    }
                }
                return response;
            };
        })()""")

        # First, try to trigger a real submission from the UI to see what headers it sends
        # Find and type in the textarea using React-compatible method
        logger.info("Finding textarea and typing prompt...")

        # Use zendriver's type method for proper React input
        textarea_found = await page.evaluate(f"""(async () => {{
            // Try multiple selectors
            const textarea = document.querySelector('textarea') ||
                           document.querySelector('[role="textbox"]') ||
                           document.querySelector('textarea[name="message"]') ||
                           document.querySelector('[data-testid="chat-input"]');
            if (!textarea) {{
                // Log what elements exist on the page
                const all = document.querySelectorAll('textarea, input[type="text"], [role="textbox"]');
                return {{ found: false, elements: Array.from(all).map(e => e.tagName + ':' + e.getAttribute('name') + ':' + e.getAttribute('role') + ':' + e.getAttribute('data-testid')) }};
            }}
            return {{ found: true, tag: textarea.tagName, name: textarea.getAttribute('name') }};
        }})()""")
        logger.info(f"Textarea search result: {textarea_found}")

        # Try using zendriver to type into the textarea
        try:
            textarea = await page.select('textarea', timeout=5)
            if textarea:
                logger.info("Found textarea via zendriver, typing...")
                await textarea.send_keys(prompt_text)
                await asyncio.sleep(0.5)

                # Find and click submit button
                submit_result = await page.evaluate("""(async () => {
                    const btns = document.querySelectorAll('button');
                    const submitBtns = Array.from(btns).filter(b => {
                        const text = b.textContent.toLowerCase();
                        const aria = b.getAttribute('aria-label')?.toLowerCase() || '';
                        const svg = b.querySelector('svg');
                        return b.type === 'submit' || text.includes('send') || text.includes('submit') || 
                               aria.includes('send') || aria.includes('submit') || (svg && b.closest('form'));
                    });
                    if (submitBtns.length > 0) {
                        submitBtns[0].click();
                        return { clicked: true, text: submitBtns[0].textContent.trim().substring(0, 50) };
                    }
                    return { clicked: false, buttons: Array.from(btns).map(b => b.textContent.trim().substring(0, 30)).slice(0, 10) };
                })()""")
                logger.info(f"Submit result: {submit_result}")

                if submit_result and isinstance(submit_result, dict) and submit_result.get("clicked"):
                    # Wait for response to be captured
                    for wait in range(60):
                        await asyncio.sleep(1)
                        result = await page.evaluate("""(function() {
                            if (window.__lastEvalResponse) return JSON.stringify(window.__lastEvalResponse);
                            if (window.__lastEvalError) return JSON.stringify({type: 'fetch_error', error: window.__lastEvalError});
                            return null;
                        })()""")
                        if result:
                            break
                    else:
                        yield {"type": "error", "error": "Timeout waiting for UI response"}
                        return

                    logger.info(f"UI response captured (len={len(result) if result else 0})")
                else:
                    logger.warning(f"Could not find submit button: {submit_result}")
                    # Fall through to direct fetch approach
                    textarea = None
            else:
                logger.warning("Could not find textarea via zendriver")
        except Exception as e:
            logger.warning(f"UI submission failed: {e}")
            textarea = None

        if not textarea:
            # Fall back to direct fetch approach
            logger.info("Falling back to direct fetch approach...")
            logger.info(f"Request data: {json.dumps(data)}")

            # Log captured headers from any previous real browser request
            captured_headers = await page.evaluate("window.__capturedHeaders")
            if captured_headers:
                logger.info(f"Previously captured real browser headers: {captured_headers}")

            result = await page.evaluate(
                f"""(async () => {{
                    try {{
                        const response = await window.__origFetch('/nextjs-api/stream/create-evaluation', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Accept': 'text/x-component',
                            }},
                            credentials: 'include',
                            body: JSON.stringify({json.dumps(data)})
                        }});

                        const status = response.status;
                        const headers = {{}};
                        response.headers.forEach((v, k) => {{ headers[k] = v; }});

                        if (!response.ok) {{
                            const text = await response.text();
                            return JSON.stringify({{
                                type: 'error',
                                status: status,
                                headers: headers,
                                body: text.substring(0, 5000)
                            }});
                        }}

                        const reader = response.body.getReader();
                        const decoder = new TextDecoder();
                        let result = '';
                        while (true) {{
                            const {{ done, value }} = await reader.read();
                            if (done) break;
                            result += decoder.decode(value, {{ stream: true }});
                        }}
                        return JSON.stringify({{
                            type: 'success',
                            status: status,
                            headers: headers,
                            body: result
                        }});
                    }} catch (err) {{
                        return JSON.stringify({{ type: 'fetch_error', error: err.toString() }});
                    }}
                }})()""",
                await_promise=True
            )

            logger.info(f"Response length: {len(result) if result else 0}")

            if not result:
                yield {"type": "error", "error": "Empty response from browser fetch"}
                return

        # Parse the response
        try:
            parsed = json.loads(result)
            # Handle both UI capture format {status, body, url} and fetch format {type, status, headers, body}
            resp_type = parsed.get("type")
            status = parsed.get("status", 0)
            response_body = parsed.get("body", "")

            logger.info(f"Response type: {resp_type}, status: {status}, body length: {len(response_body)}")

            if resp_type == "fetch_error":
                yield {"type": "error", "error": f"Fetch error: {parsed.get('error', 'unknown')}"}
                return

            if resp_type == "error" or status >= 400:
                logger.error(f"API error {status}: {response_body[:500]}")
                if status == 401:
                    yield {"type": "error", "error": "Login required! Please log into arena.ai and try again."}
                elif status == 429:
                    yield {"type": "error", "error": f"Model busy (429): {response_body[:200]}"}
                else:
                    yield {"type": "error", "error": f"Error {status}: {response_body[:200]}"}
                return

            logger.info(f"Response body (first 2000 chars): {response_body[:2000]}")
        except json.JSONDecodeError:
            response_body = result

        # Parse the response body
        has_content = False
        if response_body:
            for line in response_body.split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    if line.startswith("a0:"):
                        chunk = json.loads(line[3:])
                        if isinstance(chunk, str) and chunk == "hasArenaError":
                            yield {"type": "error", "error": "Arena error"}
                            return
                        if isinstance(chunk, str):
                            has_content = True
                            yield {"type": "text", "text": chunk}
                        elif isinstance(chunk, list):
                            for item in chunk:
                                if isinstance(item, dict) and "text" in item:
                                    has_content = True
                                    yield {"type": "text", "text": item.get("text", "")}
                    elif line.startswith("ag:"):
                        chunk = json.loads(line[3:])
                        if isinstance(chunk, str):
                            yield {"type": "thought", "thought": chunk}
                    elif line.startswith("a2:"):
                        chunk = json.loads(line[3:])
                        if isinstance(chunk, list):
                            images = [item.get("image") for item in chunk if isinstance(item, dict) and item.get("image")]
                            if images:
                                yield {"type": "images", "images": images}
                    elif line.startswith("ad:"):
                        finish_data = json.loads(line[3:])
                        if "usage" in finish_data:
                            yield {"type": "usage", "usage": finish_data["usage"]}
                        yield {"type": "final", "finish_reason": "stop"}
                        return
                    elif line.startswith("a3:"):
                        error_data = json.loads(line[3:])
                        yield {"type": "error", "error": f"Arena error: {error_data}"}
                        return
                except json.JSONDecodeError:
                    continue

        if not has_content:
            yield {"type": "error", "error": "Empty response"}
        yield {"type": "final", "finish_reason": "stop"}

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info(f"generate_stream called: model={model!r}, has_nodriver={has_nodriver}")

        if not has_nodriver:
            yield {"type": "error", "error": "zendriver is required. Install with: pip install zendriver"}
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
                yield {"type": "error", "error": "No models available"}
                return

        prompt = ""
        # Find the actual user message (not system prompts disguised as user messages)
        for msg in reversed(messages):
            content = msg.get("content", "")
            if isinstance(content, str):
                role = msg.get("role", "")
                # Skip system-style prompts even if sent as "user" role
                if content.startswith("You are ") and len(content) > 500:
                    continue
                prompt = content
                break

        if not prompt and messages:
            prompt = messages[-1].get("content", "")
            if isinstance(prompt, str) and prompt.startswith("You are ") and len(prompt) > 500:
                # Last resort: just use a simple prompt
                prompt = "Hello"

        logger.info(f"Sending prompt (len={len(prompt)}): {prompt[:200]}...")

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
        }
        if model_id:
            data["modelAId"] = model_id

        async for chunk in self.make_request_via_browser(data, proxy):
            yield chunk