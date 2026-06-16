import codecs
import json
import logging
import random
import re
import uuid
from typing import Any, AsyncGenerator, Dict, List

from curl_cffi import CurlFollow, CurlHttpVersion
from curl_cffi.requests import AsyncSession
from .base import BaseProvider

logger = logging.getLogger("flashy.gemini")

GEMINI_MODELS: List[Dict[str, Any]] = [
    {
        "id": "gemini-3-flash",
        "name": "Gemini 3 Flash",
        "model_id": "fbb127bbb056c959",
        "model_number": 1,
        "capabilities": {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True},
        "tier": "free",
    },
    {
        "id": "gemini-3-pro",
        "name": "Gemini 3 Pro",
        "model_id": "9d8ca3786ebdfbea",
        "model_number": 3,
        "capabilities": {"chat": True, "stream": True, "vision": True, "reasoning": True, "tools": True},
        "tier": "advanced",
    },
    {
        "id": "gemini-3-lite",
        "name": "Gemini 3 Lite",
        "model_id": "cf41b0e0dd7d53e5",
        "model_number": 6,
        "capabilities": {"chat": True, "stream": True, "vision": True, "reasoning": False, "tools": True},
        "tier": "free",
    },
]

ENDPOINT_INIT = "https://gemini.google.com/app"
ENDPOINT_GENERATE = "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"

MODEL_HEADER_KEY = "x-goog-ext-525001261-jspb"
MODEL_DEFAULT_METADATA = ["", "", "", None, None, None, None, None, None, ""]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
]


def _build_model_header(model_id: str, model_number: int) -> Dict[str, str]:
    return {
        MODEL_HEADER_KEY: json.dumps([
            1, None, None, None, model_id, None, None, 0,
            [4, 5, 6, 8], None, None, 1, None, None, model_number,
        ]),
        "x-goog-ext-73010989-jspb": "[0]",
        "x-goog-ext-73010990-jspb": "[0,0,0]",
    }


class _StreamingFrameParser:
    def __init__(self):
        self.buffer = ""
        self.prefix_checked = False

    def _skip_until_json(self):
        for i, c in enumerate(self.buffer):
            if c in ("[", "{"):
                if i > 0:
                    self.buffer = self.buffer[i:]
                return True
        return False

    def _extract_one_frame(self) -> str | None:
        if not self._skip_until_json():
            return None
        depth = 0
        in_string = False
        escape = False
        for i, c in enumerate(self.buffer):
            if escape:
                escape = False
                continue
            if c == "\\" and in_string:
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c in ("[", "{"):
                depth += 1
            elif c in ("]", "}"):
                depth -= 1
                if depth == 0:
                    end = i + 1
                    while end < len(self.buffer) and self.buffer[end] in " \t\r\n":
                        end += 1
                    frame = self.buffer[:end]
                    self.buffer = self.buffer[end:]
                    return frame
        return None

    def feed(self, content: str) -> list:
        if content:
            self.buffer += content
        if not self.prefix_checked:
            self._strip_prefix()
        parsed = []
        while True:
            frame = self._extract_one_frame()
            if frame is None:
                break
            frame = frame.strip()
            if not frame:
                continue
            try:
                p = json.loads(frame)
            except json.JSONDecodeError:
                continue
            if isinstance(p, list) and len(p) == 1:
                parsed.append(p[0])
            else:
                parsed.append(p)
        return parsed

    def flush(self) -> list:
        return self.feed("")

    def _strip_prefix(self):
        if self.prefix_checked:
            return
        prefix = ")]}'"
        if len(self.buffer) < len(prefix) and prefix.startswith(self.buffer):
            return
        if self.buffer.startswith(prefix):
            self.buffer = self.buffer[len(prefix):].lstrip()
        self.prefix_checked = True


class GeminiProvider(BaseProvider):
    def __init__(self, cookie: str = "", cookie_ts: str = "", cookies_json: str = ""):
        self._cookie = cookie
        self._cookie_ts = cookie_ts
        self._cookies_json = cookies_json
        self._session: AsyncSession | None = None

    async def _ensure_session(self) -> AsyncSession:
        if self._session is None:
            self._session = AsyncSession(
                impersonate="chrome",
                allow_redirects=CurlFollow.SAFE,
                http_version=CurlHttpVersion.V3,
            )
        return self._session

    def _apply_cookies(self, session: AsyncSession):
        if self._cookies_json:
            try:
                data = json.loads(self._cookies_json)
                cookies_list = data if isinstance(data, list) else data.get("cookies", data)
                if isinstance(cookies_list, dict):
                    for name, value in cookies_list.items():
                        if value:
                            session.cookies.set(name, value, domain=".google.com", path="/")
                elif isinstance(cookies_list, list):
                    for c in cookies_list:
                        if isinstance(c, dict) and c.get("name") and c.get("value"):
                            session.cookies.set(
                                c["name"], c["value"],
                                domain=c.get("domain", ".google.com"),
                                path=c.get("path", "/"),
                            )
            except json.JSONDecodeError:
                pass
        if self._cookie:
            session.cookies.set("__Secure-1PSID", self._cookie, domain=".google.com")
        if self._cookie_ts:
            session.cookies.set("__Secure-1PSIDTS", self._cookie_ts, domain=".google.com")

    async def _get_access_token(self) -> tuple[str, str, str]:
        session = await self._ensure_session()
        self._apply_cookies(session)
        response = await session.get(ENDPOINT_INIT, headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Origin": "https://gemini.google.com",
            "Referer": "https://gemini.google.com/",
            "User-Agent": random.choice(USER_AGENTS),
        })
        html = response.text
        snlm0e = re.search(r'"SNlM0e":\s*"(.*?)"', html)
        build = re.search(r'"cfb2h":\s*"(.*?)"', html)
        sid = re.search(r'"FdrFJe":\s*"(.*?)"', html)
        token = snlm0e.group(1) if snlm0e else ""
        build_label = build.group(1) if build else ""
        session_id = sid.group(1) if sid else ""
        return token, build_label, session_id

    async def generate_stream(
        self, messages: List[Dict[str, str]], model: str, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not self._cookie and not self._cookies_json:
            yield {"error": "Gemini requires Google cookies (__Secure-1PSID + __Secure-1PSIDTS). Configure them in settings."}
            return

        model_cfg = GEMINI_MODELS[0]
        for m in GEMINI_MODELS:
            if m["id"] == model:
                model_cfg = m
                break

        session = await self._ensure_session()
        token, build_label, session_id = await self._get_access_token()
        if not token:
            yield {"error": "Failed to authenticate with Google. Your cookie may be expired."}
            return

        prompt = messages[-1]["content"] if messages else ""

        _reqid = random.randint(10000, 99999)
        msg_content = [prompt, 0, None, None, None, None, 0]
        uuid_str = str(uuid.uuid4()).upper()
        inner_req = [None] * 81
        inner_req[0] = msg_content
        inner_req[1] = ["en"]
        inner_req[2] = MODEL_DEFAULT_METADATA
        inner_req[6] = [1]
        inner_req[7] = 1
        inner_req[10] = 1
        inner_req[11] = 0
        inner_req[17] = [[0]]
        inner_req[18] = 0
        inner_req[27] = 1
        inner_req[30] = [4]
        inner_req[41] = [1]
        inner_req[53] = 0
        inner_req[61] = []
        inner_req[68] = 1
        inner_req[79] = model_cfg["model_number"]
        inner_req[80] = 1
        inner_req[59] = uuid_str

        model_headers = _build_model_header(model_cfg["model_id"], model_cfg["model_number"])
        model_header_parsed = json.loads(model_headers[MODEL_HEADER_KEY])
        model_header_parsed.append(1)
        model_header_parsed.append(session_id)
        model_headers[MODEL_HEADER_KEY] = json.dumps(model_header_parsed)

        request_headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Origin": "https://gemini.google.com",
            "Referer": "https://gemini.google.com/",
            "User-Agent": random.choice(USER_AGENTS),
            **model_headers,
            "x-goog-ext-525005358-jspb": json.dumps([uuid_str, 1]),
            "X-Same-Domain": "1",
        }

        params = {"hl": "en", "_reqid": _reqid, "rt": "c"}
        if build_label:
            params["bl"] = build_label

        payload_freq = json.dumps([None, json.dumps(inner_req)])

        try:
            async with session.stream(
                "POST",
                ENDPOINT_GENERATE,
                params=params,
                headers=request_headers,
                data={"at": token, "f.req": payload_freq},
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    yield {"error": f"Gemini returned HTTP {resp.status_code}: {body[:200]}"}
                    return

                parser = _StreamingFrameParser()
                decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
                full_text = ""
                thought_text = ""

                async for chunk in resp.aiter_content():
                    decoded = decoder.decode(chunk, final=False)
                    frames = parser.feed(decoded)
                    for frame in frames:
                        inner_str = _get_path(frame, [2])
                        if not inner_str or not isinstance(inner_str, str):
                            continue
                        try:
                            part = json.loads(inner_str)
                        except json.JSONDecodeError:
                            continue
                        candidates = _get_path(part, [4], [])
                        if not candidates:
                            continue
                        for c in candidates:
                            if not isinstance(c, list):
                                continue
                            text = _get_path(c, [1, 0], "")
                            thoughts = _get_path(c, [37, 0, 0], "")
                            if thoughts and len(thoughts) > len(thought_text):
                                delta = thoughts[len(thought_text):]
                                if delta:
                                    yield {"thought": delta}
                                thought_text = thoughts
                            if text and len(text) > len(full_text):
                                delta = text[len(full_text):]
                                if delta:
                                    yield {"text": delta}
                                full_text = text

                final = decoder.decode(b"", final=True)
                frames = parser.feed(final)
                frames.extend(parser.flush())
                for frame in frames:
                    inner_str = _get_path(frame, [2])
                    if not inner_str or not isinstance(inner_str, str):
                        continue
                    try:
                        part = json.loads(inner_str)
                    except json.JSONDecodeError:
                        continue
                    candidates = _get_path(part, [4], [])
                    if not candidates:
                        continue
                    for c in candidates:
                        if not isinstance(c, list):
                            continue
                        text = _get_path(c, [1, 0], "")
                        thoughts = _get_path(c, [37, 0, 0], "")
                        if thoughts and len(thoughts) > len(thought_text):
                            delta = thoughts[len(thought_text):]
                            if delta:
                                yield {"thought": delta}
                            thought_text = thoughts
                        if text and len(text) > len(full_text):
                            delta = text[len(full_text):]
                            if delta:
                                yield {"text": delta}
                            full_text = text

                yield {"is_final": True, "finish_reason": "stop"}

        except Exception as e:
            logger.exception(f"[GEMINI] Stream error: {e}")
            yield {"error": f"Gemini request failed: {e}"}

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return GEMINI_MODELS


def _get_path(data, path, default=None):
    current = data
    for key in path:
        if isinstance(key, int):
            if isinstance(current, list) and 0 <= key < len(current):
                current = current[key]
            else:
                return default
        elif isinstance(key, str):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        else:
            return default
    return current if current is not None else default
