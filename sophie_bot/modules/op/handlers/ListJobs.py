from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from apscheduler.job import Job
from stfu_tg import KeyValue, Section, VList

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.scheduler import scheduler


class ListJobsHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("op_listjobs"), IsOP(True)

    async def handle(self) -> Any:
        jobs: list[Job] = scheduler.get_jobs()

        doc = Section(VList(*(KeyValue(job.name, job.next_run_time) for job in jobs)), title="Awaiting jobs")

        await self.event.reply(doc.to_html())
