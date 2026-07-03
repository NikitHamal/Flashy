import json
import logging
from typing import Any, Dict, Optional

from curl_cffi.requests import AsyncSession

from .base import BaseOAuthAdapter
from .types import OAuthResult, TokenValidationResult

logger = logging.getLogger("flashy.oauth")


class OAuthManager:
    """Manages token validation and refresh across providers."""

    def __init__(self):
        self._adapters: Dict[str, BaseOAuthAdapter] = {}

    def register_adapter(self, provider_id: str, adapter: BaseOAuthAdapter):
        self._adapters[provider_id] = adapter

    def get_adapter(self, provider_id: str) -> Optional[BaseOAuthAdapter]:
        return self._adapters.get(provider_id)

    async def validate(self, provider_id: str, credentials: Dict[str, str]) -> TokenValidationResult:
        adapter = self.get_adapter(provider_id)
        if not adapter:
            return TokenValidationResult(valid=False, error=f"No adapter for {provider_id}")
        return await adapter.validate_token(credentials)

    async def refresh(self, provider_id: str, credentials: Dict[str, str]) -> Optional[Dict[str, str]]:
        adapter = self.get_adapter(provider_id)
        if not adapter:
            return None
        return await adapter.refresh_token(credentials)


class DeepSeekAdapter(BaseOAuthAdapter):
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        token = credentials.get("token", "")
        if not token:
            return TokenValidationResult(valid=False, error="No token provided")
        try:
            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.get(
                    "https://chat.deepseek.com/api/v0/users/current",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    biz = data.get("data", {}).get("biz_data", {})
                    return TokenValidationResult(
                        valid=True,
                        token_type="token",
                        account_info={
                            "id": str(biz.get("id", "")),
                            "email": biz.get("email", ""),
                            "name": biz.get("name", ""),
                        },
                    )
                return TokenValidationResult(valid=False, error=f"Validation failed: {resp.status_code}")
        except Exception as e:
            return TokenValidationResult(valid=False, error=str(e))


class GLMAdapter(BaseOAuthAdapter):
    SIGN_SECRET = "8a1317a7468aa3ad86e997d08f3f31cb"

    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        refresh_token = credentials.get("token", "") or credentials.get("refresh_token", "")
        if not refresh_token:
            return TokenValidationResult(valid=False, error="No refresh token provided")
        try:
            import hashlib, time
            ts = str(int(time.time()))
            nonce = hashlib.md5(ts.encode()).hexdigest()[:8]
            sign = hashlib.md5(f"{ts}-{nonce}-{self.SIGN_SECRET}".encode()).hexdigest()

            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    "https://chatglm.cn/chatglm/user-api/user/refresh",
                    headers={
                        "Authorization": f"Bearer {refresh_token}",
                        "X-Sign": sign,
                        "X-Timestamp": ts,
                        "X-Nonce": nonce,
                        "Content-Type": "application/json",
                    },
                    json={},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return TokenValidationResult(valid=True, token_type="refresh_token")
                return TokenValidationResult(valid=False, error=f"Validation failed: {resp.status_code}")
        except Exception as e:
            return TokenValidationResult(valid=False, error=str(e))


class MiniMaxAdapter(BaseOAuthAdapter):
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        import hashlib, time, uuid

        token = credentials.get("token", "")
        real_user_id = credentials.get("real_user_id", "")

        if not token:
            return TokenValidationResult(valid=False, error="No token provided")

        jwt_token = token
        user_id = real_user_id

        if "+" in token and not user_id:
            parts = token.split("+", 1)
            user_id, jwt_token = parts

        if not user_id:
            payload = self.parse_jwt(jwt_token)
            if payload:
                user_id = payload.get("user", {}).get("id", "")

        if not user_id:
            return TokenValidationResult(valid=False, error="Cannot determine user_id from token")

        try:
            ts = str(int(time.time()))
            data_json = json.dumps({
                "device_id": str(uuid.uuid4()),
                "user_id": user_id,
                "token": jwt_token,
                "device_name": "Chrome",
                "device_type": "web",
                "app_version": "1.0.0",
            }, separators=(",", ":"), ensure_ascii=False)

            x_signature = hashlib.md5((ts + jwt_token + data_json).encode()).hexdigest()

            async with AsyncSession(impersonate="chrome") as session:
                resp = await session.post(
                    "https://agent.minimaxi.com/v1/api/user/device/register",
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "x-signature": x_signature,
                        "x-ts": ts,
                        "Content-Type": "application/json",
                    },
                    data=data_json,
                    timeout=15,
                )
                if resp.status_code == 200:
                    return TokenValidationResult(valid=True, token_type="jwt")
                return TokenValidationResult(valid=False, error=f"Validation failed: {resp.status_code}")
        except Exception as e:
            return TokenValidationResult(valid=False, error=str(e))


class MimoAdapter(BaseOAuthAdapter):
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        service_token = credentials.get("service_token", "")
        user_id = credentials.get("user_id", "")
        ph_token = credentials.get("ph_token", "")

        if not service_token or not user_id or not ph_token:
            missing = [k for k, v in [("service_token", service_token), ("user_id", user_id), ("ph_token", ph_token)] if not v]
            return TokenValidationResult(valid=False, error=f"Missing required tokens: {', '.join(missing)}")

        return TokenValidationResult(
            valid=True,
            token_type="cookie",
            account_info={"user_id": user_id},
        )


class PerplexityAdapter(BaseOAuthAdapter):
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        session_token = credentials.get("session_token", "") or credentials.get("token", "")
        if not session_token:
            return TokenValidationResult(valid=False, error="No session token provided")
        if len(session_token) < 50:
            return TokenValidationResult(valid=False, error="Session token too short, likely invalid")
        return TokenValidationResult(valid=True, token_type="cookie")


class QwenAdapter(BaseOAuthAdapter):
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        ticket = credentials.get("ticket", "") or credentials.get("token", "")
        if not ticket:
            return TokenValidationResult(valid=False, error="No SSO ticket provided")
        return TokenValidationResult(valid=True, token_type="cookie")


class QwenAiAdapter(BaseOAuthAdapter):
    async def validate_token(self, credentials: Dict[str, str]) -> TokenValidationResult:
        token = credentials.get("token", "")
        if not token:
            return TokenValidationResult(valid=False, error="No token provided")
        is_jwt = self.is_jwt(token)
        return TokenValidationResult(
            valid=is_jwt or len(token) > 20,
            token_type="jwt" if is_jwt else "token",
        )


def create_adapter(provider_id: str) -> BaseOAuthAdapter:
    adapters = {
        "deepseekai": DeepSeekAdapter,
        "deepseek": DeepSeekAdapter,
        "glm": GLMAdapter,
        "minimax": MiniMaxAdapter,
        "mimo": MimoAdapter,
        "perplexity": PerplexityAdapter,
        # DEPRECATED: Qwen provider blocked by Aliyun WAF captcha
        # "qwen": QwenAdapter,
        # "qwen-ai": QwenAiAdapter,
        # "qwenai": QwenAiAdapter,
    }
    cls = adapters.get(provider_id)
    if cls:
        return cls(provider_id)
    raise ValueError(f"No OAuth adapter for provider: {provider_id}")


oauth_manager = OAuthManager()

for pid in ["deepseekai", "deepseek", "glm", "minimax", "mimo", "perplexity"]:
    try:
        oauth_manager.register_adapter(pid, create_adapter(pid))
    except ValueError:
        pass
