from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from aiogram import Dispatcher
from fastapi import FastAPI

from sophie_bot.api.routes import api_router
from sophie_bot.config import CONFIG
from sophie_bot.startup import start_init
from sophie_bot.utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up Sophie API...")

    dp = Dispatcher()
    await start_init(dp)
    yield
    log.info("Shutting down Sophie API...")


app = FastAPI(title="Sophie API", lifespan=lifespan)
app.include_router(api_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Sophie API is running"}


def start_rest_mode() -> None:
    uvicorn.run(app, host=CONFIG.api_listen, port=CONFIG.api_port)
