from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class OAuthResult:
    success: bool
    provider_id: str = ""
    credentials: Dict[str, str] = field(default_factory=dict)
    account_info: Optional[Dict[str, str]] = None
    error: str = ""


@dataclass
class TokenValidationResult:
    valid: bool
    token_type: str = "jwt"
    expires_at: Optional[int] = None
    account_info: Optional[Dict[str, str]] = None
    error: str = ""


@dataclass
class ManualTokenConfig:
    provider_id: str
    token_type: str
    label: str
    placeholder: str
    description: str
    help_url: str = ""
    fields: List[Dict[str, str]] = field(default_factory=list)


MANUAL_TOKEN_CONFIGS: Dict[str, List[ManualTokenConfig]] = {
    "deepseekai": [
        ManualTokenConfig(
            provider_id="deepseekai",
            token_type="token",
            label="User Token",
            placeholder="Enter the userToken from DeepSeek browser",
            description="Open DevTools on chat.deepseek.com, find userToken in Application > Local Storage",
            help_url="https://chat.deepseek.com",
        ),
    ],
    "glm": [
        ManualTokenConfig(
            provider_id="glm",
            token_type="refresh_token",
            label="Refresh Token",
            placeholder="Enter GLM refresh token",
            description="Get refresh_token from chatglm.cn, found in DevTools > Application > Local Storage",
            help_url="https://chatglm.cn",
        ),
    ],
    "minimax": [
        ManualTokenConfig(
            provider_id="minimax",
            token_type="token",
            label="JWT Token (realUserID_token)",
            placeholder="Format: realUserID+JWTtoken or just JWT",
            description="Get from agent.minimaxi.com Local Storage: _token (JWT) and user_detail_agent (realUserID)",
            help_url="https://agent.minimaxi.com",
        ),
    ],
    "mimo": [
        ManualTokenConfig(
            provider_id="mimo",
            token_type="cookie",
            label="Service Token",
            placeholder="serviceToken from Cookie",
            description="Get from aistudio.xiaomimimo.com Cookies in DevTools",
            help_url="https://aistudio.xiaomimimo.com",
            fields=[
                {"name": "service_token", "label": "Service Token", "type": "password"},
                {"name": "user_id", "label": "User ID", "type": "text"},
                {"name": "ph_token", "label": "PH Token", "type": "password"},
            ],
        ),
    ],
    "perplexity": [
        ManualTokenConfig(
            provider_id="perplexity",
            token_type="cookie",
            label="Session Token",
            placeholder="__Secure-next-auth.session-token",
            description="Get __Secure-next-auth.session-token from perplexity.ai Cookies",
            help_url="https://www.perplexity.ai",
        ),
    ],
    # DEPRECATED: Qwen provider blocked by Aliyun WAF captcha
    # "qwen": [
    #     ManualTokenConfig(
    #         provider_id="qwen",
    #         token_type="cookie",
    #         label="SSO Ticket",
    #         placeholder="tongyi_sso_ticket",
    #         description="Get tongyi_sso_ticket from www.qianwen.com Cookies",
    #         help_url="https://www.qianwen.com",
    #     ),
    # ],
    # "qwen-ai": [
    #     ManualTokenConfig(
    #         provider_id="qwen-ai",
    #         token_type="jwt",
    #         label="Auth Token",
    #         placeholder="JWT token from chat.qwen.ai",
    #         description="Get token from chat.qwen.ai Local Storage (key: 'token')",
    #         help_url="https://chat.qwen.ai",
    #     ),
    # ],
}
