from asyncio import sleep

from sophie_bot.modules.utils_.scheduler import SophieSchedulerABC
from sophie_bot.utils.logger import log


class WelcomeSecurityScheduler(SophieSchedulerABC):
    async def handle(self):
        while True:
            log.info("WelcomeSecurityScheduler")
            await sleep(3)
            log.info("WelcomeSecurityScheduler after")
