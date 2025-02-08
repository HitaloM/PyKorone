import asyncio

from aiogram import Dispatcher

from sophie_bot.services.scheduler import scheduler, scheduler_loop
from sophie_bot.startup import start_init


async def scheduler_init():
    await start_init(dp=Dispatcher())


def start_scheduler_mode():
    asyncio.set_event_loop(scheduler_loop)
    scheduler_loop.run_until_complete(scheduler_init())

    scheduler.start()

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        scheduler_loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
