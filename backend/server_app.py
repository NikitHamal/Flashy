import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import openai
from .routers import qwen


def create_server_app() -> FastAPI:
    app = FastAPI(title="Flashy Provider Server", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(openai.router)
    app.include_router(qwen.router)

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

    uvicorn.run(
        "backend.server_app:app",
        host=os.environ.get("FLASHY_PROVIDER_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASHY_PROVIDER_PORT", "8001")),
        reload=os.environ.get("FLASHY_RELOAD", "0").lower() in {"1", "true", "yes"},
    )
