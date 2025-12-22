from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from aiogram import Dispatcher
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sophie_bot.config import CONFIG
from sophie_bot.startup import start_init
from sophie_bot.utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up Sophie API...")

    dp = Dispatcher()
    await start_init(dp)

    from sophie_bot.modules import LOADED_API_ROUTERS

    for router in LOADED_API_ROUTERS:
        app.include_router(router)

    yield
    log.info("Shutting down Sophie API...")


app = FastAPI(title="Sophie API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def start_rest_mode() -> None:
    uvicorn.run(app, host=CONFIG.api_listen, port=CONFIG.api_port)
