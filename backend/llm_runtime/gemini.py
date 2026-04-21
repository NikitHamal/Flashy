import asyncio

from gemini_webapi import GeminiClient

from ..config import load_config
from ..storage import get_chat_metadata
from .helpers import resolve_gemini_model


async def get_gemini_client(service) -> GeminiClient:
    if not hasattr(service, "_init_lock"):
        service._init_lock = asyncio.Lock()

    async with service._init_lock:
        if service.gemini_client is None:
            service.config = load_config()
            psid = service.config.get("Secure_1PSID", "").strip()
            psidts = service.config.get("Secure_1PSIDTS", "").strip()

            service.gemini_client = GeminiClient(
                secure_1psid=psid,
                secure_1psidts=psidts,
                proxy=None
            )
            try:
                await service.gemini_client.init(
                    timeout=30,
                    auto_close=False,
                    close_delay=300,
                    auto_refresh=False,
                )
            except Exception:
                service.gemini_client = None
                raise

        return service.gemini_client


async def get_gemini_chat_session(service, session_id: str, history=None, fresh: bool = False):
    client = await get_gemini_client(service)

    if session_id not in service.sessions or fresh:
        model_name = service.config.get("model", "G_2_5_FLASH")
        model = resolve_gemini_model(model_name)
        saved_meta = get_chat_metadata(session_id) if not fresh else None
        if saved_meta:
            chat = client.start_chat(
                model=model,
                cid=saved_meta.get("cid"),
                rid=saved_meta.get("rid"),
                rcid=saved_meta.get("rcid"),
            )
        else:
            chat = client.start_chat(model=model)
        service.sessions[session_id] = chat

    return service.sessions[session_id]


async def send_with_retry(
    service,
    chat,
    message: str,
    files=None,
    max_retries: int = 3,
    timeout: int = 120,
    provider: str = "gemini",
    session_id: str = None,
):
    if provider != "gemini":
        raise RuntimeError("send_with_retry is Gemini-only")

    last_error = None
    current_chat = chat

    for attempt in range(max_retries):
        try:
            if files:
                response = await asyncio.wait_for(
                    current_chat.send_message(message, files=files), timeout=timeout
                )
            else:
                response = await asyncio.wait_for(
                    current_chat.send_message(message), timeout=timeout
                )

            if session_id and current_chat != chat:
                service.sessions[session_id] = current_chat
            return response

        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            last_error = f"Request timed out after {timeout}s"
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
        except Exception as exc:
            last_error = str(exc)
            error_str = str(exc).lower()
            if "invalid response" in error_str or "failed to generate" in error_str:
                if session_id and attempt < max_retries - 1:
                    try:
                        current_chat = await get_gemini_chat_session(service, session_id, fresh=True)
                        service.sessions[session_id] = current_chat
                        if len(message) > 50:
                            message = f"[System: Connection lost. Resuming task.]\n\n{message}"
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
            else:
                raise

    raise Exception(f"Failed after {max_retries} attempts: {last_error}")
