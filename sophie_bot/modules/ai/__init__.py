from aiogram import F, Router

from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.fsm.pm import AI_PM_STOP_TEXT, AiPMFSM
from sophie_bot.modules.ai.handlers.ai_cmd import AiCmd
from sophie_bot.modules.ai.handlers.pm import AiPmHandle, AiPmInitialize, AiPmStop
from sophie_bot.modules.ai.handlers.reply import AiReplyHandler
from sophie_bot.modules.ai.middlewares.cache_messages import CacheMessagesMiddleware
from sophie_bot.utils.i18n import lazy_gettext as l_

router = Router(name="ai")

__module_name__ = l_("Sophie AI")
__module_emoji__ = "✨"
__module_description__ = l_("Rainbow sparkles and shininess")
__module_info__ = l_("Please note that you can make a limited amount of AI requests per day.")


def __pre_setup__():
    router.message.outer_middleware(CacheMessagesMiddleware())

    router.message.register(AiReplyHandler, AiReplyHandler.filter, AIThrottleFilter())

    router.message.register(AiPmInitialize, CMDFilter("ai"), ChatTypeFilter("private"))
    router.message.register(AiPmStop, F.text == AI_PM_STOP_TEXT, ChatTypeFilter("private"))

    router.message.register(AiPmHandle, AiPMFSM.in_ai, ChatTypeFilter("private"), AIThrottleFilter())

    router.message.register(AiCmd, CMDFilter("ai"))
