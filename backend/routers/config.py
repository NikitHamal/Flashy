from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from ..config import load_config, save_config

router = APIRouter()

class ConfigUpdate(BaseModel):
    Secure_1PSID: Optional[str] = None
    Secure_1PSIDTS: Optional[str] = None
    Secure_1PSIDCC: Optional[str] = None
    GITHUB_PAT: Optional[str] = None
    model: Optional[str] = None
    active_provider: Optional[str] = None
    deepinfra_api_key: Optional[str] = None
    glm_api_key: Optional[str] = None
    glm_user_id: Optional[str] = None
    qwen_api_key: Optional[str] = None

@router.get("/config")
async def get_config():
    return load_config()

@router.post("/config")
async def update_config(data: ConfigUpdate, request: Request):
    current_config = load_config()
    new_data = {k: v for k, v in data.dict().items() if v is not None}
    current_config.update(new_data)
    save_config(current_config)
    
    # Reset service client
    if hasattr(request.app.state, "gemini_service"):
        await request.app.state.gemini_service.reset()
        
    return {"message": "Config updated and client reset"}
