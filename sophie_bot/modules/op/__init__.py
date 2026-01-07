from aiogram import Router
from fastapi import APIRouter

from sophie_bot.modules.op.handlers.Banner import OpBannerHandler
from sophie_bot.modules.op.handlers.ButtonsTest import ButtonsTestHandler
from sophie_bot.modules.op.handlers.Captcha import OpCaptchaHandler
from sophie_bot.modules.op.handlers.KillSwitch import KillSwitchHandler
from sophie_bot.modules.op.handlers.ListJobs import ListJobsHandler
from sophie_bot.modules.op.handlers.StopJobs import StopJobsHandler
from .api import health_router

api_router = APIRouter()
api_router.include_router(health_router)

__all__ = ["api_router"]

router = Router(name="op")

__exclude_public__ = True

__handlers__ = (
    ListJobsHandler,
    StopJobsHandler,
    KillSwitchHandler,
    OpBannerHandler,
    OpCaptchaHandler,
    ButtonsTestHandler,
)
