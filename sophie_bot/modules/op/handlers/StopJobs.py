from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from apscheduler.job import Job

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.scheduler import scheduler


class StopJobsHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_stopjobs"), IsOP(True)

    async def handle(self) -> Any:
        jobs: list[Job] = scheduler.get_jobs()

        for job in jobs:
            scheduler.remove_job(job.id)

        await self.event.reply("All scheduled jobs have been stopped.")
