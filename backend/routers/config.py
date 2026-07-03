from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from ..config import load_config, save_config

router = APIRouter()

class ConfigUpdate(BaseModel):
    GITHUB_PAT: Optional[str] = None
    model: Optional[str] = None
    active_provider: Optional[str] = "qwen"
    deepinfra_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    grok_proxy: Optional[str] = None
    glm_refresh_token: Optional[str] = None
    chat2api_base_url: Optional[str] = None
    chat2api_api_key: Optional[str] = None
    lmarena_cookies: Optional[str] = None
    chatx_cookie: Optional[str] = None
    chatx_base_url: Optional[str] = None
    unimodel_api_key: Optional[str] = None
    unimodel_base_url: Optional[str] = None
    reasoning_effort: Optional[str] = None
    bai_api_key: Optional[str] = None
    bai_base_url: Optional[str] = None
    openmodel_api_key: Optional[str] = None
    openmodel_base_url: Optional[str] = None
    paxsenix_api_key: Optional[str] = None
    paxsenix_base_url: Optional[str] = None
    zenmux_api_key: Optional[str] = None
    zenmux_base_url: Optional[str] = None
    mistral_api_key: Optional[str] = None
    mistral_base_url: Optional[str] = None
    babestown_api_key: Optional[str] = None
    babestown_base_url: Optional[str] = None

@router.get("/config")
async def get_config():
    return load_config()

@router.post("/config")
async def update_config(data: ConfigUpdate, request: Request):
    current_config = load_config()
    new_data = {k: v for k, v in data.dict().items() if v is not None}
    current_config.update(new_data)
    save_config(current_config)

    # Reset service client to apply new config
    if hasattr(request.app.state, "llm_service"):
        await request.app.state.llm_service.reset()

    return {"message": "Config updated and client reset"}
