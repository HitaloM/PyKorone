from aiogram import Router

from ...filters.chat_status import ChatTypeFilter
from ...filters.cmd import CMDFilter
from .handlers.privacy import PrivacyInfo

router = Router(name="pm_menu")


def __pre_setup__():
    router.message.register(PrivacyInfo, CMDFilter("privacy"), ChatTypeFilter("private"))
