from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from aiogram import Dispatcher
from fastapi import FastAPI

from sophie_bot.config import CONFIG
from sophie_bot.services.rest import app, init_api_routers
from sophie_bot.startup import start_init
from sophie_bot.utils.logger import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting up Sophie API...")

    dp = Dispatcher()
    await start_init(dp)

    init_api_routers(app)

    yield
    log.info("Shutting down Sophie API...")


app.router.lifespan_context = lifespan


def start_rest_mode() -> None:
    uvicorn.run(app, host=CONFIG.api_listen, port=CONFIG.api_port)
