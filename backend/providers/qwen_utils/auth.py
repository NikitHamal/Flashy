import logging
import re
from typing import Dict, Optional

from curl_cffi.requests import AsyncSession
from .cookie_generator import generate_cookies, get_cookies
from .generate_ua import BXUAGenerator

logger = logging.getLogger("flashy.qwen.auth")

QWEN_URL = "https://chat.qwen.ai"

_ua_generator = BXUAGenerator()


def build_session_headers(bx_ua: str = "") -> Dict[str, str]:
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": QWEN_URL,
        "referer": f"{QWEN_URL}/",
        "sec-ch-ua": '"Google Chrome";v="136", "Chromium";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
        "x-source": "web",
    }
    if bx_ua:
        headers["bx-ua"] = bx_ua
    return headers


async def prepare_cookies() -> Dict[str, str]:
    try:
        cookies_data = await get_cookies()
        if not cookies_data.get("ssxmod_itna"):
            raise ValueError("empty cache")
    except Exception:
        cookies_data = generate_cookies()

    safe_cookies = {}
    for k, v in cookies_data.items():
        safe_cookies[k] = str(v) if not isinstance(v, str) else v
    return safe_cookies


def generate_bx_ua(cookies_data: Dict[str, str]) -> str:
    raw_fingerprint = cookies_data.get("rawData") or ""
    if not raw_fingerprint:
        return ""
    try:
        return _ua_generator.generate(raw_fingerprint)
    except Exception as e:
        logger.warning(f"[QWEN] Failed to generate bx-ua: {e}")
        return ""


def check_waf_response(resp):
    """Check if a response indicates a WAF/captcha block."""
    if resp.status_code == 403:
        return "Access forbidden - possible WAF block"
    if resp.status_code in (503, 520, 521, 522, 523, 524, 525, 526, 527, 529, 530):
        return f"Cloudflare/WAF error (HTTP {resp.status_code})"
    if resp.status_code == 200:
        # Some WAFs return 200 with HTML captcha pages
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            try:
                text = resp.text if hasattr(resp, "text") else ""
                lower_text = text.lower()
                if any(k in lower_text for k in ("aliyun_waf_aa", "captcha", "blocked", "verification", "challenge")):
                    return "WAF/Captcha page returned"
            except Exception:
                pass
    return None


async def get_midtoken(session: AsyncSession, proxy: str = None, force_refresh: bool = False):
    midtoken = getattr(get_midtoken, "_cached", None)
    uses = getattr(get_midtoken, "_uses", 0)

    if midtoken and uses < 50 and not force_refresh:
        get_midtoken._uses = uses + 1
        return midtoken

    try:
        r = await session.get("https://sg-wum.alibaba.com/w/wu.json", proxy=proxy)
        if r.status_code == 200:
            match = re.search(r"(?:umx\.wu|__fycb)\('([^']+)'\)", r.text)
            if match:
                get_midtoken._cached = match.group(1)
                get_midtoken._uses = 1
                logger.info(f"[QWEN] New midtoken obtained: {match.group(1)[:20]}...")
                return match.group(1)
    except Exception as e:
        logger.warning(f"[QWEN] Error fetching midtoken: {e}")

    return None