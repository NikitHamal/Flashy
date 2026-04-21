import hashlib
import hmac
import logging
import mimetypes
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib.parse import quote

from curl_cffi.requests import AsyncSession

logger = logging.getLogger("flashy.qwen.upload")

QWEN_URL = "https://chat.qwen.ai"

_FILE_TYPE_MAP = {
    ".png": ("image", "image", "vision"),
    ".jpg": ("image", "image", "vision"),
    ".jpeg": ("image", "image", "vision"),
    ".gif": ("image", "image", "vision"),
    ".webp": ("image", "image", "vision"),
    ".bmp": ("image", "image", "vision"),
    ".svg": ("image", "image", "vision"),
    ".mp4": ("video", "video", "video"),
    ".avi": ("video", "video", "video"),
    ".mov": ("video", "video", "video"),
    ".mkv": ("video", "video", "video"),
    ".webm": ("video", "video", "video"),
    ".mp3": ("audio", "audio", "audio"),
    ".wav": ("audio", "audio", "audio"),
    ".ogg": ("audio", "audio", "audio"),
    ".flac": ("audio", "audio", "audio"),
    ".aac": ("audio", "audio", "audio"),
    ".m4a": ("audio", "audio", "audio"),
}

_file_cache: Dict[str, dict] = {}


def classify_file(file_name: str, mime_type: str):
    ext = os.path.splitext(file_name)[1].lower()
    if ext in _FILE_TYPE_MAP:
        return _FILE_TYPE_MAP[ext]
    return (mime_type, "file", "document")


def build_oss_headers(method: str, date_str: str, sts_data: dict, content_type: str) -> dict:
    bucket_name = sts_data.get("bucketname", "qwen-webui-prod")
    file_path = sts_data.get("file_path", "")
    access_key_id = sts_data.get("access_key_id")
    access_key_secret = sts_data.get("access_key_secret")
    security_token = sts_data.get("security_token")

    headers = {
        "Content-Type": content_type,
        "x-oss-content-sha256": "UNSIGNED-PAYLOAD",
        "x-oss-date": date_str,
        "x-oss-security-token": security_token,
        "x-oss-user-agent": "aliyun-sdk-js/6.23.0 Chrome 132.0.0.0 on Windows 10 64-bit",
    }

    headers_lower = {k.lower(): v for k, v in headers.items()}
    canonical_headers_list = []
    signed_headers_list = []
    required_headers = [
        "content-md5", "content-type", "x-oss-content-sha256",
        "x-oss-date", "x-oss-security-token", "x-oss-user-agent",
    ]

    for header_name in sorted(required_headers):
        if header_name in headers_lower:
            canonical_headers_list.append(f"{header_name}:{headers_lower[header_name]}")
            signed_headers_list.append(header_name)

    canonical_headers = "\n".join(canonical_headers_list) + "\n"
    canonical_uri = f"/{bucket_name}/{quote(file_path, safe='/')}"
    canonical_request = f"{method}\n{canonical_uri}\n\n{canonical_headers}\n\nUNSIGNED-PAYLOAD"

    date_parts = date_str.split("T")
    date_scope = f"{date_parts[0]}/ap-southeast-1/oss/aliyun_v4_request"
    string_to_sign = (
        f"OSS4-HMAC-SHA256\n{date_str}\n{date_scope}\n"
        f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    )

    def sign(key, msg):
        return hmac.new(key, msg.encode() if isinstance(msg, str) else msg, hashlib.sha256).digest()

    date_key = sign(f"aliyun_v4{access_key_secret}".encode(), date_parts[0])
    region_key = sign(date_key, "ap-southeast-1")
    service_key = sign(region_key, "oss")
    signing_key = sign(service_key, "aliyun_v4_request")
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    headers["authorization"] = (
        f"OSS4-HMAC-SHA256 Credential={access_key_id}/{date_scope},Signature={signature}"
    )
    return headers


async def upload_file(
    file_path: str,
    session: AsyncSession,
    cookies: dict,
    headers: dict,
    proxy: str = None,
) -> Optional[dict]:
    if not os.path.isfile(file_path):
        logger.warning(f"[QWEN] File not found: {file_path}")
        return None

    file_data = open(file_path, "rb").read()
    file_size = len(file_data)
    file_name = os.path.basename(file_path)

    mime_type, _ = mimetypes.guess_type(file_name)
    if not mime_type:
        mime_type = "application/octet-stream"

    content_hash = hashlib.md5(file_data).hexdigest()
    if content_hash in _file_cache:
        logger.info(f"[QWEN] Using cached file: {file_name}")
        return _file_cache[content_hash]

    file_type, show_type, file_class = classify_file(file_name, mime_type)

    try:
        sts_resp = await session.post(
            f"{QWEN_URL}/api/v2/files/getstsToken",
            json={
                "filename": file_name,
                "filesize": file_size,
                "filetype": mime_type,
            },
            headers=headers,
            proxy=proxy,
        )
        if sts_resp.status_code != 200:
            logger.warning(f"[QWEN] STS token request failed: {sts_resp.status_code}")
            return None

        sts_data = sts_resp.json()
        if not sts_data.get("success"):
            logger.warning(f"[QWEN] STS token error: {sts_data}")
            return None

        data = sts_data.get("data", {})
        file_url = data.get("file_url", "")
        file_id = data.get("file_id", "")

        date_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        oss_headers = build_oss_headers("PUT", date_str, data, mime_type)

        upload_resp = await session.put(
            file_url.split("?")[0],
            data=file_data,
            headers=oss_headers,
            proxy=proxy,
        )
        if upload_resp.status_code not in (200, 204):
            logger.warning(f"[QWEN] File upload failed: {upload_resp.status_code}")
            return None

        now_ms = int(time.time() * 1000)
        file_obj = {
            "type": file_type,
            "file": {
                "created_at": now_ms,
                "data": {},
                "filename": file_name,
                "hash": None,
                "id": file_id,
                "meta": {
                    "name": file_name,
                    "size": file_size,
                    "content_type": mime_type,
                },
                "update_at": now_ms,
            },
            "id": file_id,
            "url": file_url,
            "name": file_name,
            "collection_name": "",
            "progress": 0,
            "status": "uploaded",
            "greenNet": "success",
            "size": file_size,
            "error": "",
            "itemId": str(uuid.uuid4()),
            "file_type": mime_type,
            "showType": show_type,
            "file_class": file_class,
            "uploadTaskId": str(uuid.uuid4()),
        }

        _file_cache[content_hash] = file_obj
        logger.info(f"[QWEN] File uploaded: {file_name} ({file_size} bytes, id={file_id})")
        return file_obj

    except Exception as e:
        logger.warning(f"[QWEN] File upload error: {e}")
        return None