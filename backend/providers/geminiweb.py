"""Gemini Web provider — gemini.google.com anonymous chat (free Flash-Lite).

No login, no cookies, no API key: a fresh browser identity is created per
request by warming ``GET /app`` (collecting NID/COMPASS cookies and parsing
WIZ_global_data for f.sid + bl), then posting the StreamGenerate form. The
big client-side conversation token is NOT required for anonymous chats — an
empty string works. Responses are length-prefixed JSON chunks; answer text
lives in nested ``rc_*`` arrays and is cumulative, so only deltas are emitted.

Multi-turn: server returns conversation/response ids (``c_*`` / ``r_*``) which
are threaded back through the ``conversation`` kwarg like other providers.
"""

import asyncio
import json
import logging
import random
import re
import urllib.parse
import uuid
from typing import AsyncGenerator, Any, Dict, List, Optional

from curl_cffi.requests import AsyncSession

from .base import BaseProvider
from .response_types import Error, error_to_dict

logger = logging.getLogger("flashy.geminiweb")

BASE_URL = "https://gemini.google.com"
APP_PATH = "/app"
STREAM_ENDPOINT = "/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
REQUEST_TIMEOUT = 300
MAX_RETRIES = 3

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"

MODELS = [
    {"id": "gemini-flash-lite", "name": "Gemini Flash Lite (Web)", "vision": False,
     "tools": True, "context_window": 32000},
]
MODEL_MAP = {m["id"]: m for m in MODELS}
DEFAULT_MODEL = MODELS[0]["id"]


def _resolve_model(model: str) -> str:
    m = (model or "").strip()
    if m in MODEL_MAP:
        return m
    low = m.lower()
    for mid in MODEL_MAP:
        if low == mid.lower() or mid.lower().endswith("/" + low) or low.endswith(mid.split("/")[-1].lower()):
            return mid
    return DEFAULT_MODEL


class _GeminiWebSession:
    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy
        self.session: Optional[AsyncSession] = None
        self.fsid = ""
        self.bl = "boq_assistant-bard-web-server_20260819.10_p0"
        self.conversation_id = ""
        self.response_id = ""
        self.reqid = random.randint(100000, 999999)

    async def warm(self) -> bool:
        self.session = AsyncSession(impersonate="chrome", timeout=REQUEST_TIMEOUT)
        try:
            resp = await self.session.get(
                BASE_URL + APP_PATH,
                headers={"user-agent": _UA, "accept": "text/html"},
                proxy=self.proxy,
            )
            if resp.status_code != 200:
                logger.warning("[GEMINIWEB] warm GET failed: %s", resp.status_code)
                return False
            html = resp.text
            m = re.search(r'"FdrFJe":"([0-9\-]+)"', html)
            if m:
                self.fsid = m.group(1)
            m = re.search(r"(boq_assistant-bard-web-server_[0-9._p]+)", html)
            if m:
                self.bl = m.group(1)
            m = re.search(r'"SNlM0e":"([^"]+)"', html)
            self._snlm0e = m.group(1) if m else ""
            if not self.fsid:
                logger.warning("[GEMINIWEB] warm: FdrFJe not found")
                return False
            return True
        except Exception as exc:
            logger.warning("[GEMINIWEB] warm error: %s", exc)
            return False

    def _build_inner(self, prompt: str) -> str:
        return json.dumps([
            [prompt, 0, None, None, None, None, 0],
            ["en-US"],
            ["", "", "", None, None, None, None, None, None, ""],
            "",
            uuid.uuid4().hex,
            None,
            [0],
            1,
            None,
            None,
            1,
            0,
        ])

    async def send(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        self.reqid += 100000
        inner = self._build_inner(prompt)
        freq = json.dumps([None, inner])
        url = (
            f"{BASE_URL}{STREAM_ENDPOINT}?bl={self.bl}&f.sid={self.fsid}"
            f"&hl=en-US&_reqid={self.reqid}&rt=c"
        )
        snlm0e = getattr(self, '_snlm0e', '')
        if snlm0e:
            url += f"&at={urllib.parse.quote(snlm0e, safe='')}"
        headers = {
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "origin": BASE_URL,
            "referer": f"{BASE_URL}/",
            "user-agent": _UA,
            "x-same-domain": "1",
        }
        resp = await self.session.post(
            url,
            data=f"f.req={urllib.parse.quote(freq, safe='')}&".encode("utf-8"),
            headers=headers,
            proxy=self.proxy,
            stream=True,
        )
        if resp.status_code != 200:
            txt = ""
            try:
                txt = (await resp.atext())[:500]
            except Exception:
                pass
            if "er" in txt and "400" in txt:
                yield {"error": "GeminiWeb rejected the request (400). Retrying may help; if persistent the page format may have changed."}
            else:
                yield {"error": f"GeminiWeb HTTP {resp.status_code}: {txt[:300]}"}
            return

        saw_any = False
        prev_text = ""
        buffer = ""
        async for chunk_bytes in resp.aiter_content():
            buffer += chunk_bytes.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip("\r")
                if not line or line.startswith(")]}'") or line.isdigit():
                    continue
                if not line.startswith("["):
                    continue
                for ev in self._parse_chunk(line):
                    if ev.get("type") == "text":
                        snap = ev["content"]
                        if snap.startswith(prev_text):
                            delta = snap[len(prev_text):]
                        elif not prev_text:
                            delta = snap
                        else:
                            delta = ""
                        if len(snap) > len(prev_text):
                            prev_text = snap
                        if delta:
                            saw_any = True
                            yield {"text": delta}
                    else:
                        yield ev
        if not saw_any:
            yield {"error": "GeminiWeb stream ended without content"}
            return
        yield {"is_final": True, "finish_reason": "stop"}

    def _parse_chunk(self, line: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        try:
            arr = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            return out
        if not isinstance(arr, list):
            return out
        for entry in arr:
            if not isinstance(entry, list) or not entry or entry[0] != "wrb.fr":
                continue
            inner_raw = entry[2] if len(entry) > 2 else None
            if not isinstance(inner_raw, str):
                continue
            try:
                inner = json.loads(inner_raw)
            except (json.JSONDecodeError, ValueError):
                continue
            if not isinstance(inner, list) or len(inner) < 5:
                continue
            ids = inner[1]
            if isinstance(ids, list) and len(ids) >= 2:
                cid, rid = ids[0], ids[1]
                if isinstance(cid, str) and cid.startswith("c_"):
                    self.conversation_id = cid
                if isinstance(rid, str) and rid.startswith("r_"):
                    self.response_id = rid
            body = inner[4]
            if not isinstance(body, list):
                continue
            for part in body:
                if isinstance(part, list) and part and isinstance(part[0], str) and part[0].startswith("rc_"):
                    texts = part[1]
                    if isinstance(texts, list):
                        best = ""
                        for t in texts:
                            if isinstance(t, str) and len(t) > len(best):
                                best = t
                        if best.strip():
                            out.append({"type": "text", "content": best})
        return out

    def close(self):
        try:
            if self.session is not None:
                closer = getattr(self.session, "aclose", None) or self.session.close
                result = closer()
                if hasattr(result, "__await__"):
                    import asyncio as _aio
                    try:
                        loop = _aio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(result)
                        else:
                            loop.run_until_complete(result)
                    except Exception:
                        pass
        except Exception:
            pass


class GeminiWebProvider(BaseProvider):
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        original = model
        model = _resolve_model(model)
        logger.info("[GEMINIWEB] %s -> %s messages=%d", original, model, len(messages))


        history = [m for m in messages if m.get("role") != "system"]
        system_prefix = ""
        for m in messages:
            if m.get("role") == "system" and isinstance(m.get("content"), str):
                system_prefix = m["content"][:4000]
                break
        prompt = history[-1].get("content", "") if history else ""
        if system_prefix:
            prompt = f"{system_prefix}\n\n{prompt}"[:12000]
        if len(history) > 1:
            transcript = []
            for m in history[:-1][-10:]:
                role = "User" if m.get("role") == "user" else "Assistant"
                content = m.get("content", "")
                if isinstance(content, str) and content.strip():
                    transcript.append(f"{role}: {content[:2000]}")
            if transcript:
                prompt = "Previous conversation:\n" + "\n".join(transcript) + f"\n\nUser: {prompt}"

        proxy = kwargs.get("proxy")
        last_error = "unknown error"
        for attempt in range(MAX_RETRIES):
            gsession = _GeminiWebSession(proxy=proxy)
            try:
                warmed = await gsession.warm()
                if not warmed:
                    last_error = "could not warm session"
                    continue
                got_error = None
                async for ev in gsession.send(prompt):
                    if "error" in ev:
                        got_error = ev["error"]
                        break
                    yield ev
                if got_error is None:
                    return
                last_error = got_error
                if "HTTP 5" in got_error or "429" in got_error:
                    await asyncio.sleep(2 ** attempt + random.random())
                    continue
                if "400" in got_error and attempt == 0:
                    await asyncio.sleep(1 + random.random())
                    continue
                yield {"error": got_error}
                return
            except Exception as exc:
                last_error = f"request failed: {exc}"
                logger.warning("[GEMINIWEB] attempt %d failed: %s", attempt + 1, exc)
                await asyncio.sleep(1 + random.random())
            finally:
                gsession.close()
        yield {"error": f"GeminiWeb: {last_error}"}

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        out = []
        for m in MODELS:
            out.append({
                "id": m["id"],
                "name": m["name"],
                "capabilities": {"vision": m["vision"], "thinking": False, "tools": m["tools"]},
                "max_context": m["context_window"],
                "context_window": m["context_window"],
                "pricing": {"cents_per_input_token": 0, "cents_per_output_token": 0},
            })
        return out
