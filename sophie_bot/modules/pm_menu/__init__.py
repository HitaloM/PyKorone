from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.chat_status import ChatTypeFilter
from ...filters.cmd import CMDFilter
from .handlers.privacy import PrivacyInfo

router = Router(name="pm_menu")


__module_name__ = l_("Information")
__module_emoji__ = "ℹ️"


def __pre_setup__():
    router.message.register(PrivacyInfo, CMDFilter("privacy"), ChatTypeFilter("private"))
