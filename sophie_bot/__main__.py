import tracemalloc

from sophie_bot.config import CONFIG
from sophie_bot.modes import SOPHIE_MODE, SophieModes
from sophie_bot.utils.logger import log
from sophie_bot.utils.sentry import init_sentry

# Import misc stuff
if CONFIG.sentry_url:
    init_sentry()


if CONFIG.memory_debug:
    log.warning("Enabling memory debug!")
    tracemalloc.start()

if SOPHIE_MODE == SophieModes.bot:
    from sophie_bot.modes.bot import start_bot_mode

    log.info("Starting the bot mode...")
    start_bot_mode()

elif SOPHIE_MODE == SophieModes.scheduler:
    from sophie_bot.modes.scheduler import start_scheduler_mode

    log.info("Starting the scheduler mode...")
    start_scheduler_mode()
