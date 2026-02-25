from aiogram import Router
from aiogram.utils.chat_action import ChatActionMiddleware
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import DevicePageCallback as DevicePageCallback
from .callbacks import GetDeviceCallback as GetDeviceCallback
from .handlers.get import DeviceGetCallbackHandler
from .handlers.list import DeviceListCallbackHandler
from .handlers.search import DeviceSearchHandler

router = Router(name="gsm_arena")

__module_name__ = l_("GSM Arena")
__module_emoji__ = "📱"
__module_description__ = l_("Search device specifications on GSMArena")
__module_info__ = LazyProxy(
    lambda: Doc(l_("Search for smartphones and get a quick overview of their specifications directly from GSMArena."))
)

__handlers__ = (DeviceSearchHandler, DeviceListCallbackHandler, DeviceGetCallbackHandler)


def __pre_setup__() -> None:
    router.message.middleware(ChatActionMiddleware())
