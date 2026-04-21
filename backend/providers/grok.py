import re
import asyncio
import hashlib
import json
import logging
import os
import random
import time
from base64 import b64encode, b64decode
from dataclasses import dataclass, field
from math import floor, copysign, pi, cos, sin
from re import findall, search, sub
from secrets import token_bytes, token_hex
from struct import pack
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from bs4 import BeautifulSoup
from curl_cffi import CurlMime
from curl_cffi.requests import AsyncSession
from ecdsa import SigningKey, SECP256k1

from .base import BaseProvider

logger = logging.getLogger("flashy.grok")

GROK_RENDER_RE = re.compile(r'<grok:render[^>]*>.*?</grok:render>', re.DOTALL)
GROK_RENDER_OPEN_RE = re.compile(r'<grok:render[^>]*>', re.DOTALL)
GROK_TAG_RE = re.compile(r'</?grok:render[^>]*>', re.DOTALL)


def _clean_grok_response(text: str) -> str:
    if not text:
        return text
    text = GROK_RENDER_RE.sub('', text)
    text = GROK_RENDER_OPEN_RE.sub('', text)
    text = GROK_TAG_RE.sub('', text)
    return text.strip()

MAPPINGS_DIR = os.path.join(os.path.dirname(__file__), "grok_mappings")

MODELS = [
    {"id": "grok-3-auto", "name": "Grok 3 Auto"},
    {"id": "grok-3-fast", "name": "Grok 3 Fast"},
    {"id": "grok-4", "name": "Grok 4"},
    {"id": "grok-4-mini-thinking-tahoe", "name": "Grok 4 Mini Thinking"},
]

MODEL_MODES = {
    "grok-3-auto": ("MODEL_MODE_AUTO", "auto"),
    "grok-3-fast": ("MODEL_MODE_FAST", "fast"),
    "grok-4": ("MODEL_MODE_EXPERT", "expert"),
    "grok-4-mini-thinking-tahoe": ("MODEL_MODE_GROK_4_MINI_THINKING", "grok-4-mini-thinking"),
}

BROWSER_HEADERS = [
    {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "accept-encoding": "gzip, deflate, br, zstd",
    },
]


def _between(text: str, start: str, end: str) -> str:
    return text.split(start)[1].split(end)[0]


def _generate_keys() -> dict:
    sk = SigningKey.generate(curve=SECP256k1)
    priv_bytes = sk.to_string()
    pub_bytes = sk.get_verifying_key().to_string("compressed")
    return {
        "privateKey": b64encode(priv_bytes).decode(),
        "userPublicKey": list(pub_bytes),
    }


def _sign_challenge(challenge_data: bytes, key_b64: str) -> dict:
    key_bytes = b64decode(key_b64)
    sk = SigningKey.from_string(key_bytes, curve=SECP256k1)
    digest = hashlib.sha256(challenge_data).digest()
    signature = sk.sign_digest(digest)
    return {
        "challenge": b64encode(challenge_data).decode(),
        "signature": b64encode(signature).decode(),
    }


def _to_hex(num: float) -> str:
    rounded = round(float(num), 2)
    if rounded == 0.0:
        return "0"
    sign = "-" if copysign(1.0, rounded) < 0 else ""
    absval = abs(rounded)
    intpart = int(floor(absval))
    frac = absval - intpart
    if frac == 0.0:
        return sign + format(intpart, "x")
    frac_digits = []
    f = frac
    for _ in range(20):
        f *= 16
        digit = int(floor(f + 1e-12))
        frac_digits.append(format(digit, "x"))
        f -= digit
        if abs(f) < 1e-12:
            break
    frac_str = "".join(frac_digits).rstrip("0")
    if not frac_str:
        return sign + format(intpart, "x")
    return sign + format(intpart, "x") + "." + frac_str


def _h(x: float, param: float, c: float, e: bool):
    f = ((x * (c - param)) / 255.0) + param
    if e:
        return floor(f)
    rounded = round(float(f), 2)
    return 0.0 if rounded == 0.0 else rounded


def _cubic_bezier(t: float, x1: float, y1: float, x2: float, y2: float) -> float:
    def bezier(u: float):
        omu = 1.0 - u
        b1 = 3.0 * omu * omu * u
        b2 = 3.0 * omu * u * u
        b3 = u * u * u
        return b1 * x1 + b2 * x2 + b3, b1 * y1 + b2 * y2 + b3
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if bezier(mid)[0] < t:
            lo = mid
        else:
            hi = mid
    u = 0.5 * (lo + hi)
    return bezier(u)[1]


def _simulate_style(values: list, c: int) -> dict:
    duration = 4096
    current_time = round(c / 10.0) * 10
    t = current_time / duration
    cp = [_h(v, -1 if (i % 2) else 0, 1, False) for i, v in enumerate(values[7:])]
    eased_y = _cubic_bezier(t, cp[0], cp[1], cp[2], cp[3])
    start = [float(x) for x in values[0:3]]
    end = [float(x) for x in values[3:6]]
    r = round(start[0] + (end[0] - start[0]) * eased_y)
    g = round(start[1] + (end[1] - start[1]) * eased_y)
    b = round(start[2] + (end[2] - start[2]) * eased_y)
    color = f"rgb({r}, {g}, {b})"
    end_angle = _h(values[6], 60, 360, True)
    angle = end_angle * eased_y
    rad = angle * pi / 180.0
    cosv = cos(rad)
    sinv = sin(rad)
    a = int(round(cosv)) if abs(cosv - round(cosv)) < 1e-7 else f"{cosv:.6f}"
    d = int(round(cosv)) if abs(cosv - round(cosv)) < 1e-7 else f"{cosv:.6f}"
    bval = int(round(sinv)) if abs(sinv - round(sinv)) < 1e-7 else f"{sinv:.7f}"
    cval = int(round(-sinv)) if abs(-sinv - round(-sinv)) < 1e-7 else f"{(-sinv):.7f}"
    transform = f"matrix({a}, {bval}, {cval}, {d}, 0, 0)"
    return {"color": color, "transform": transform}


def _xa(svg: str) -> list:
    substr = svg[9:]
    parts = substr.split("C")
    out = []
    for part in parts:
        cleaned = sub(r"[^\d]+", " ", part).strip()
        nums = [int(tok) for tok in cleaned.split() if tok] if cleaned else [0]
        out.append(nums)
    return out


def _generate_sign(path: str, method: str, verification: str, svg: str, x_values: list) -> str:
    n = int(time.time() - 1682924400)
    t = pack('<I', n)
    r = b64decode(verification)
    arr_rx = _xa(svg)
    idx = list(r)[x_values[0]] % 16
    c = ((list(r)[x_values[1]] % 16) * (list(r)[x_values[2]] % 16)) * (list(r)[x_values[3]] % 16)
    vals = arr_rx[idx]
    k = _simulate_style(vals, c)
    concat = str(k["color"]) + str(k["transform"])
    matches = findall(r"[\d\.\-]+", concat)
    converted = [_to_hex(float(m)) for m in matches]
    joined = "".join(converted).replace(".", "").replace("-", "")
    msg = "!".join([method, path, str(n)]) + "obfiowerehiring" + joined
    digest = hashlib.sha256(msg.encode('utf-8')).digest()[:16]
    prefix_byte = int(floor(random.random() * 256))
    assembled = bytes([prefix_byte]) + r + t + digest + bytes([3])
    arr = bytearray(assembled)
    if len(arr) > 0:
        first = arr[0]
        for i in range(1, len(arr)):
            arr[i] = arr[i] ^ first
    return b64encode(bytes(arr)).decode('ascii').replace('=', '')


def _load_mappings(filename: str):
    filepath = os.path.join(MAPPINGS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return [] if filename == "grok.json" else {}


def _save_mappings(filename: str, data):
    os.makedirs(MAPPINGS_DIR, exist_ok=True)
    filepath = os.path.join(MAPPINGS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


class GrokSession:
    def __init__(self, model: str = "grok-3-auto", proxy: str = None):
        self.model = model
        self.mode_tuple = MODEL_MODES.get(model, ("MODEL_MODE_AUTO", "auto"))
        self.proxy = proxy
        self.session: Optional[AsyncSession] = None
        self.cookies: dict = {}
        self.actions: list = []
        self.xsid_script: str = ""
        self.baggage: str = ""
        self.sentry_trace: str = ""
        self.anon_user: str = ""
        self.keys: dict = {}
        self.verification_token: str = ""
        self.anim: int = 0
        self.svg_data: str = ""
        self.numbers: list = []
        self.c_run: int = 0
        self.conversation_id: Optional[str] = None
        self.parent_response_id: Optional[str] = None
        self._initialized = False
        self._lock = asyncio.Lock()

    async def _ensure_session(self):
        if self.session is None:
            self.session = AsyncSession(impersonate="chrome136", default_headers=False)
            if self.proxy:
                proxies = {"all": self.proxy} if self.proxy else None
                self.session.proxies = proxies

    async def initialize(self):
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            await self._ensure_session()
            self.keys = _generate_keys()
            await self._load_site()
            await self._c_request_step0()
            await self._c_request_step1()
            await self._c_request_step2()
            self._initialized = True

    async def _load_site(self):
        headers = BROWSER_HEADERS[0].copy()
        headers["upgrade-insecure-requests"] = "1"
        headers["priority"] = "u=0, i"
        resp = await self.session.get('https://grok.com/c', headers=headers)
        self.cookies.update(dict(resp.cookies))

        soup = BeautifulSoup(resp.text, 'html.parser')
        scripts = [
            s['src'] for s in soup.find_all('script', src=True)
            if '/_next/static/chunks/' in s.get('src', '')
        ]

        self.actions, self.xsid_script = await self._parse_grok(scripts)
        self.baggage = _between(resp.text, '<meta name="baggage" content="', '"')
        self.sentry_trace = _between(resp.text, '<meta name="sentry-trace" content="', '-')

    async def _parse_grok(self, scripts: list) -> tuple:
        grok_mapping = _load_mappings("grok.json")
        for entry in grok_mapping:
            if entry.get("action_script") in scripts:
                return entry["actions"], entry["xsid_script"]

        action_script = None
        script_content1 = None
        script_content2 = None
        for script in scripts:
            url = script if script.startswith('http') else f'https://grok.com{script}'
            try:
                content_resp = await self.session.get(url)
                content = content_resp.text
                if "anonPrivateKey" in content:
                    script_content1 = content
                    action_script = script
                elif "880932)" in content:
                    script_content2 = content
            except Exception:
                continue

        if not script_content1 or not script_content2:
            raise RuntimeError("Failed to parse Grok scripts")

        actions = findall(r'createServerReference\)\("([a-f0-9]+)"', script_content1)
        xsid_script_match = search(r'"(static/chunks/[^"]+\.js)"[^}]*?\(880932\)', script_content2)
        xsid_script = xsid_script_match.group(1) if xsid_script_match else ""

        if actions and xsid_script:
            grok_mapping.append({
                "action_script": action_script,
                "actions": actions,
                "xsid_script": xsid_script,
            })
            _save_mappings("grok.json", grok_mapping)
            return actions, xsid_script

        raise RuntimeError("Failed to extract actions and xsid_script from Grok")

    async def _c_request_step0(self):
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "next-action": self.actions[0],
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22c%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22%22%2C%22oc%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
            "baggage": self.baggage,
            "sentry-trace": f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
            "user-agent": BROWSER_HEADERS[0]["user-agent"],
            "accept": "text/x-component",
            "origin": "https://grok.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://grok.com/c",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
        }

        mime = CurlMime()
        mime.addpart(
            name="1",
            data=bytes(self.keys["userPublicKey"]),
            filename="blob",
            content_type="application/octet-stream",
        )
        mime.addpart(name="0", filename=None, data='[{"userPublicKey":"$o1"}]')

        resp = await self.session.post(
            "https://grok.com/c",
            headers=headers,
            multipart=mime,
        )
        self.cookies.update(dict(resp.cookies))
        self.anon_user = _between(resp.text, '{"anonUserId":"', '"')
        self.c_run = 1

    async def _c_request_step1(self):
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "next-action": self.actions[1],
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22c%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22%22%2C%22oc%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
            "baggage": self.baggage,
            "sentry-trace": f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
            "user-agent": BROWSER_HEADERS[0]["user-agent"],
            "content-type": "text/plain;charset=UTF-8",
            "accept": "text/x-component",
            "origin": "https://grok.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://grok.com/c",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
        }
        data = json.dumps([{"anonUserId": self.anon_user}])
        resp = await self.session.post("https://grok.com/c", headers=headers, data=data)
        self.cookies.update(dict(resp.cookies))

        start_idx = resp.content.hex().find("3a6f38362c")
        challenge_bytes = None
        if start_idx != -1:
            start_idx += len("3a6f38362c")
            end_idx = resp.content.hex().find("313a", start_idx)
            if end_idx != -1:
                challenge_hex = resp.content.hex()[start_idx:end_idx]
                challenge_bytes = bytes.fromhex(challenge_hex)

        if challenge_bytes:
            self.challenge_dict = _sign_challenge(challenge_bytes, self.keys["privateKey"])
        self.c_run = 2

    async def _c_request_step2(self):
        headers = {
            "sec-ch-ua-platform": '"Windows"',
            "next-action": self.actions[2],
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22c%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22%22%2C%22oc%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
            "baggage": self.baggage,
            "sentry-trace": f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
            "user-agent": BROWSER_HEADERS[0]["user-agent"],
            "content-type": "text/plain;charset=UTF-8",
            "accept": "text/x-component",
            "origin": "https://grok.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://grok.com/c",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
        }
        data = json.dumps([{"anonUserId": self.anon_user, **self.challenge_dict}])
        resp = await self.session.post("https://grok.com/c", headers=headers, data=data)
        self.cookies.update(dict(resp.cookies))

        self.verification_token = _between(resp.text, '"name":"grok-site-verification","content":"', '"')
        self.anim = int(list(b64decode(self.verification_token))[5] % 4)

        d_values = json.loads(findall(r'\[\[{"color".*?}\]\]', resp.text)[0])[self.anim]
        self.svg_data = "M 10,30 C" + " C".join(
            f" {item['color'][0]},{item['color'][1]} {item['color'][2]},{item['color'][3]} {item['color'][4]},{item['color'][5]}"
            f" h {item['deg']}"
            f" s {item['bezier'][0]},{item['bezier'][1]} {item['bezier'][2]},{item['bezier'][3]}"
            for item in d_values
        )

        if self.xsid_script:
            script_link = f'https://grok.com/_next/{self.xsid_script}'
            txid_mapping = _load_mappings("txid.json")
            if script_link in txid_mapping:
                self.numbers = txid_mapping[script_link]
            else:
                try:
                    script_resp = await self.session.get(script_link)
                    self.numbers = [int(x) for x in findall(r'x\[(\d+)\]\s*,\s*16', script_resp.text)]
                    txid_mapping[script_link] = self.numbers
                    _save_mappings("txid.json", txid_mapping)
                except Exception:
                    self.numbers = [0, 2, 8, 9]

    def _build_conversation_headers(self, path: str, method: str) -> dict:
        xsid = _generate_sign(path, method, self.verification_token, self.svg_data, self.numbers)
        return {
            "x-xai-request-id": str(uuid4()),
            "sec-ch-ua-platform": '"Windows"',
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "baggage": self.baggage,
            "sentry-trace": f'{self.sentry_trace}-{str(uuid4()).replace("-", "")[:16]}-0',
            "traceparent": f"00-{token_hex(16)}-{token_hex(8)}-00",
            "user-agent": BROWSER_HEADERS[0]["user-agent"],
            "content-type": "application/json",
            "x-statsig-id": xsid,
            "accept": "*/*",
            "origin": "https://grok.com",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://grok.com/",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
        }

    async def send_message(self, message: str, extra_data: dict = None) -> dict:
        await self.initialize()

        if extra_data:
            self.cookies = extra_data.get("cookies", self.cookies)
            self.actions = extra_data.get("actions", self.actions)
            self.xsid_script = extra_data.get("xsid_script", self.xsid_script)
            self.baggage = extra_data.get("baggage", self.baggage)
            self.sentry_trace = extra_data.get("sentry_trace", self.sentry_trace)
            self.anon_user = extra_data.get("anon_user", self.anon_user)
            self.keys["privateKey"] = extra_data.get("privateKey", self.keys.get("privateKey", ""))
            self.conversation_id = extra_data.get("conversationId")
            self.parent_response_id = extra_data.get("parentResponseId")
            await self._ensure_session()
            self.session.cookies.update(self.cookies)
            self._initialized = True

        model_mode, mode = self.mode_tuple

        if not self.conversation_id:
            path = '/rest/app-chat/conversations/new'
            method = 'POST'
            headers = self._build_conversation_headers(path, method)

            conversation_data = {
                'temporary': False,
                'modelName': self.model,
                'message': message,
                'fileAttachments': [],
                'imageAttachments': [],
                'disableSearch': False,
                'enableImageGeneration': True,
                'returnImageBytes': False,
                'returnRawGrokInXaiRequest': False,
                'enableImageStreaming': True,
                'imageGenerationCount': 2,
                'forceConcise': False,
                'toolOverrides': {},
                'enableSideBySide': True,
                'sendFinalMetadata': True,
                'isReasoning': False,
                'webpageUrls': [],
                'disableTextFollowUps': False,
                'responseMetadata': {
                    'requestModelDetails': {'modelId': self.model},
                },
                'disableMemory': False,
                'forceSideBySide': False,
                'modelMode': model_mode,
                'isAsyncChat': False,
            }

            resp = await self.session.post(
                f'https://grok.com{path}',
                headers=headers,
                json=conversation_data,
                timeout=120,
            )
        else:
            path = f'/rest/app-chat/conversations/{self.conversation_id}/responses'
            method = 'POST'
            headers = self._build_conversation_headers(path, method)

            conversation_data = {
                'message': message,
                'modelName': self.model,
                'parentResponseId': self.parent_response_id,
                'disableSearch': False,
                'enableImageGeneration': True,
                'imageAttachments': [],
                'returnImageBytes': False,
                'returnRawGrokInXaiRequest': False,
                'fileAttachments': [],
                'enableImageStreaming': True,
                'imageGenerationCount': 2,
                'forceConcise': False,
                'toolOverrides': {},
                'enableSideBySide': True,
                'sendFinalMetadata': True,
                'customPersonality': '',
                'isReasoning': False,
                'webpageUrls': [],
                'metadata': {
                    'requestModelDetails': {'modelId': self.model},
                    'request_metadata': {'model': self.model, 'mode': mode},
                },
                'disableTextFollowUps': False,
                'disableArtifact': False,
                'isFromGrokFiles': False,
                'disableMemory': False,
                'forceSideBySide': False,
                'modelMode': model_mode,
                'isAsyncChat': False,
                'skipCancelCurrentInflightRequests': False,
                'isRegenRequest': False,
            }

            resp = await self.session.post(
                f'https://grok.com{path}',
                headers=headers,
                json=conversation_data,
                timeout=120,
            )

        if 'rejected by anti-bot rules' in resp.text:
            logger.warning("[GROK] Anti-bot rejection, retrying with fresh session")
            self._initialized = False
            self.conversation_id = None
            self.parent_response_id = None
            return await self.send_message(message, extra_data=extra_data)

        if "Grok is under heavy usage" in resp.text:
            raise RuntimeError("Grok is under heavy usage, try again later")

        if "modelResponse" not in resp.text:
            raise RuntimeError(f"Grok unexpected response: {resp.text[:500]}")

        response_text = None
        stream_tokens = []
        conversation_id = None
        parent_response_id = None
        image_urls = None

        for line in resp.text.strip().split('\n'):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not self.conversation_id:
                token = data.get('result', {}).get('response', {}).get('token')
                if token:
                    stream_tokens.append(token)
                if not response_text and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('message'):
                    response_text = data['result']['response']['modelResponse']['message']
                if not conversation_id and data.get('result', {}).get('conversation', {}).get('conversationId'):
                    conversation_id = data['result']['conversation']['conversationId']
                if not parent_response_id and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('responseId'):
                    parent_response_id = data['result']['response']['modelResponse']['responseId']
                if not image_urls and data.get('result', {}).get('response', {}).get('modelResponse', {}).get('generatedImageUrls'):
                    image_urls = data['result']['response']['modelResponse']['generatedImageUrls']
            else:
                token = data.get('result', {}).get('token')
                if token:
                    stream_tokens.append(token)
                if not response_text and data.get('result', {}).get('modelResponse', {}).get('message'):
                    response_text = data['result']['modelResponse']['message']
                if not parent_response_id and data.get('result', {}).get('modelResponse', {}).get('responseId'):
                    parent_response_id = data['result']['modelResponse']['responseId']
                if not image_urls and data.get('result', {}).get('modelResponse', {}).get('generatedImageUrls'):
                    image_urls = data['result']['modelResponse']['generatedImageUrls']

        if conversation_id:
            self.conversation_id = conversation_id
        if parent_response_id:
            self.parent_response_id = parent_response_id

        return {
            "response": response_text or "",
            "stream_response": stream_tokens,
            "images": image_urls,
            "extra_data": {
                "anon_user": self.anon_user,
                "cookies": dict(self.session.cookies) if self.session else self.cookies,
                "actions": self.actions,
                "xsid_script": self.xsid_script,
                "baggage": self.baggage,
                "sentry_trace": self.sentry_trace,
                "conversationId": self.conversation_id,
                "parentResponseId": self.parent_response_id,
                "privateKey": self.keys.get("privateKey", ""),
            }
        }

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None


_sessions: Dict[str, GrokSession] = {}
_sessions_lock = asyncio.Lock()


async def _get_session(session_id: str, model: str = "grok-3-auto", proxy: str = None) -> GrokSession:
    async with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = GrokSession(model=model, proxy=proxy)
        return _sessions[session_id]


class GrokProvider(BaseProvider):
    """Grok Web API provider (free, reverse-engineered)."""

    @classmethod
    async def get_models(cls) -> List[Dict[str, Any]]:
        return [{"id": m["id"], "name": m["name"]} for m in MODELS]

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        proxy = kwargs.get("proxy")
        import hashlib as hl
        session_id = kwargs.get("session_id") or f"grok-{hl.md5(str(messages[-1:]).encode()).hexdigest()[:12]}"

        grok_model = model if model in MODEL_MODES else "grok-3-auto"
        session = await _get_session(session_id, model=grok_model, proxy=proxy)

        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            yield {"type": "error", "error": "No user message found"}
            return

        try:
            result = await session.send_message(user_message)
            response_text = _clean_grok_response(result.get("response", ""))

            if response_text:
                yield {"type": "text", "text": response_text}

            yield {"type": "final", "finish_reason": "stop", "is_final": True}

        except Exception as e:
            logger.error(f"Grok error: {e}")
            if "Anti-bot" in str(e) or "rejected" in str(e):
                session._initialized = False
                session.conversation_id = None
                session.parent_response_id = None
            yield {"type": "error", "error": str(e)}