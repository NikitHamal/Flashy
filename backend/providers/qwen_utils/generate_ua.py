import random
import time
import base64
import hashlib
import json
from typing import Dict, List, Any, Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .fingerprint import generate_fingerprint, generate_device_id, generate_hash


class BXUAGenerator:
    def __init__(self):
        self.version = "231"
        self.aes_key = None
        self.aes_iv = None

    def _generate_key_iv(self, seed_data: str) -> tuple:
        seed_hash = hashlib.sha256(seed_data.encode()).digest()
        key = seed_hash[:16]
        iv = seed_hash[16:32]
        return key, iv

    def _encrypt_aes_cbc(self, data: bytes, key: bytes, iv: bytes) -> bytes:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(data, AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return encrypted

    def _create_payload(self, fingerprint: str, timestamp: Optional[int] = None) -> Dict[str, Any]:
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        fields = fingerprint.split("^")

        payload = {
            "v": self.version,
            "ts": timestamp,
            "fp": fingerprint,
            "d": {
                "deviceId": fields[0],
                "sdkVer": fields[1],
                "lang": fields[5],
                "tz": fields[6],
                "platform": fields[10],
                "renderer": fields[12],
                "mode": fields[23],
                "vendor": fields[28],
            },
            "rnd": random.randint(1000, 9999),
            "seq": 1,
        }

        checksum_str = f"{fingerprint}{timestamp}{payload['rnd']}"
        payload["cs"] = hashlib.md5(checksum_str.encode()).hexdigest()[:8]

        return payload

    def generate(self, fingerprint: str, options: Optional[Dict[str, Any]] = None) -> str:
        if options is None:
            options = {}

        timestamp = options.get("timestamp")
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        payload = self._create_payload(fingerprint, timestamp)

        payload_json = json.dumps(payload, separators=(',', ':'))

        seed = options.get("seed", fingerprint)
        key, iv = self._generate_key_iv(seed)

        encrypted = self._encrypt_aes_cbc(payload_json.encode(), key, iv)

        encrypted_b64 = base64.b64encode(encrypted).decode()

        return f"{self.version}!{encrypted_b64}"

    def batch_generate(self, fingerprints: List[str], options: Optional[Dict[str, Any]] = None) -> List[str]:
        return [self.generate(fp, options) for fp in fingerprints]