from aiogram import Router
from aiogram.utils.chat_action import ChatActionMiddleware
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleScripts
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import DevicePageCallback as DevicePageCallback
from .callbacks import GetDeviceCallback as GetDeviceCallback
from .handlers.get import DeviceGetCallbackHandler
from .handlers.list import DeviceListCallbackHandler
from .handlers.search import DeviceSearchHandler

router = Router(name="gsm_arena")


def pre_setup() -> None:
    router.message.middleware(ChatActionMiddleware())


manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("GSM Arena"),
        icon="📱",
        summary=l_("Device specs from GSMArena"),
        description=LazyProxy(lambda: Doc(l_("Search phones and browse key specifications without leaving Telegram."))),
    ),
    router=router,
    handlers=(DeviceSearchHandler, DeviceListCallbackHandler, DeviceGetCallbackHandler),
    scripts=ModuleScripts(pre_setup=pre_setup),
)
