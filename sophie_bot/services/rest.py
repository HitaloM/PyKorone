from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sophie_bot.config import CONFIG


def create_app() -> FastAPI:
    app = FastAPI(title="Sophie API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CONFIG.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


def init_api_routers(app: FastAPI) -> None:
    from sophie_bot.modules import LOADED_API_ROUTERS

    for router in LOADED_API_ROUTERS:
        app.include_router(router)
