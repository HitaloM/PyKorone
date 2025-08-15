from aiogram import Router

from sophie_bot.modules.op.handlers.ListJobs import ListJobsHandler
from sophie_bot.modules.op.handlers.StopJobs import StopJobsHandler
from sophie_bot.modules.op.handlers.KillSwitch import KillSwitchHandler

router = Router(name="op")

__exclude_public__ = True

__handlers__ = (
    ListJobsHandler,
    StopJobsHandler,
    KillSwitchHandler,
)
