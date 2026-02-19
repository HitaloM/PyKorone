from aiogram import Router
from stfu_tg import Doc

from korone import dp
from korone.constants import AI_EMOJI
from korone.modules.ai.middlewares import CacheBotMessagesMiddleware, CacheUserMessagesMiddleware
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.ai_cmd import AiCmdHandler
from .handlers.enable_settings import AIEnableSettingsHandler
from .handlers.pm import AiPmHandle, AiPmInitialize, AiPmStop
from .handlers.reply import AiReplyHandler
from .handlers.reset_context import AIContextResetHandler

router = Router(name="ai")

__module_name__ = l_("Korone AI")
__module_emoji__ = AI_EMOJI
__module_description__ = l_("Rainbow sparkles and shininess")
__module_info__ = LazyProxy(lambda: Doc(l_("This module allows you to talk with AI models in groups or in PM mode.")))

__handlers__ = (
    AiPmInitialize,
    AiPmStop,
    AIContextResetHandler,
    AiPmHandle,
    AIEnableSettingsHandler,
    AiCmdHandler,
    AiReplyHandler,
)


def __pre_setup__() -> None:
    dp.message.middleware(CacheUserMessagesMiddleware())
    dp.message.middleware(CacheBotMessagesMiddleware())
