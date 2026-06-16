import json
import logging
import os
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import openai
from .routers import qwen
from . import duckai_control


def _setup_logging():
    log_level_name = os.environ.get("FLASHY_LOG_LEVEL", "DEBUG").upper()
    log_level = getattr(logging, log_level_name, logging.DEBUG)
    log_file = os.environ.get("FLASHY_PROVIDER_LOG_FILE")

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    flashy_loggers = [
        "flashy.qwen", "flashy.qwen.prompts", "flashy.qwen.stream",
        "flashy.qwen.auth", "flashy.qwen.upload", "flashy.qwen.models",
        "flashy.deepinfra", "flashy.lmarena", "flashy.airforce",
        "flashy.gradient", "flashy.grok", "flashy.kimi", "flashy.glm",
        "flashy.zai", "flashy.zai_free", "flashy.chat2api",
        "flashy.ai4bharat",
        "flashy.server.catalog", "flashy.openai",
        "flashy.duckai",
    ]

    handlers = []
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    handlers.append(console_handler)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
        handlers.append(file_handler)

    for name in flashy_loggers:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.handlers = []
        for h in handlers:
            logger.addHandler(h)
        logger.propagate = False


_setup_logging()


def _append_event(event: dict) -> None:
    target = os.environ.get("FLASHY_PROVIDER_EVENTS")
    if not target:
        return
    try:
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Telemetry should never break provider requests.
        pass


def create_server_app() -> FastAPI:
    app = FastAPI(title="Flashy Provider Server", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_telemetry(request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        started = time.perf_counter()
        status_code = 500
        error = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["x-flashy-request-id"] = request_id
            return response
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            _append_event(
                {
                    "id": request_id,
                    "ts": time.time(),
                    "method": request.method,
                    "path": request.url.path,
                    "query": request.url.query,
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "client": request.client.host if request.client else None,
                    "error": error,
                }
            )

    app.include_router(openai.router)
    app.include_router(qwen.router)

    @app.get("/duckai/status")
    async def duckai_status():
        return duckai_control.status()

    @app.post("/duckai/start")
    async def duckai_start():
        return duckai_control.start()

    @app.post("/duckai/stop")
    async def duckai_stop():
        return duckai_control.stop()

    @app.post("/duckai/restart")
    async def duckai_restart():
        return duckai_control.restart()

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": "flashy-provider-server"}

    @app.exception_handler(404)
    async def not_found(_, __):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    return app


app = create_server_app()


if __name__ == "__main__":
    import uvicorn

    log_config = None if os.environ.get("FLASHY_PROVIDER_LOG") else uvicorn.config.LOGGING_CONFIG
    uvicorn.run(
        "backend.server_app:app",
        host=os.environ.get("FLASHY_PROVIDER_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASHY_PROVIDER_PORT", "8001")),
        reload=True,
        access_log=True,
        log_config=log_config,
    )
