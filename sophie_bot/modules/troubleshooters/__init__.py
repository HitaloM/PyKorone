from aiogram import Router

from ...filters.cmd import CMDFilter
from .handlers.cancel import CancelState

router = Router(name="troubleshooters")


def __pre_setup__():
    router.message.register(CancelState, CMDFilter("cancel"))
