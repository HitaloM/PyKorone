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
__module_description__ = l_("Device specs from GSMArena")
__module_info__ = LazyProxy(lambda: Doc(l_("Search phones and browse key specifications without leaving Telegram.")))

__handlers__ = (DeviceSearchHandler, DeviceListCallbackHandler, DeviceGetCallbackHandler)


def __pre_setup__() -> None:
    router.message.middleware(ChatActionMiddleware())
