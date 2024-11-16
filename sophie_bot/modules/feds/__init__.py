from aiogram import Router

from sophie_bot.modules.feds.middlewares.check_fban import FedBanMiddleware

router = Router(name="info")


async def __pre_setup__():
    router.message.outer_middleware(FedBanMiddleware())
