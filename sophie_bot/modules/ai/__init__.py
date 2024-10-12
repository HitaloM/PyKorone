from aiogram import Router
from stfu_tg import Doc

from sophie_bot.modules.ai.handlers.ai_cmd import AiCmd
from sophie_bot.modules.ai.handlers.aisave import AISaveNote
from sophie_bot.modules.ai.handlers.autotranslate_setting import (
    AIAutotransStatus,
    ControlAIAutotrans,
)
from sophie_bot.modules.ai.handlers.enable_setting import AIStatus, EnableAI
from sophie_bot.modules.ai.handlers.filter import get_filter
from sophie_bot.modules.ai.handlers.pm import AiPmHandle, AiPmInitialize, AiPmStop
from sophie_bot.modules.ai.handlers.reply import AiReplyHandler
from sophie_bot.modules.ai.handlers.reset_context import AIContextReset
from sophie_bot.modules.ai.handlers.translate import AiTranslate, text_or_reply
from sophie_bot.modules.ai.middlewares.auto_translate import AiAutoTranslateMiddleware
from sophie_bot.modules.ai.middlewares.cache_bot_messages import (
    CacheBotMessagesMiddleware,
)
from sophie_bot.modules.ai.middlewares.cache_user_messages import (
    CacheUserMessagesMiddleware,
)
from sophie_bot.modules.ai.texts import AI_POLICY
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import lazy_gettext as l_

router = Router(name="ai")

__module_name__ = l_("Sophie AI")
__module_emoji__ = "✨"
__module_description__ = l_("Rainbow sparkles and shininess")
__module_info__ = LazyProxy(
    lambda: Doc(AI_POLICY, l_("Please note that you can make a limited amount of AI requests per day."))
)

__filters__ = get_filter()


def __pre_setup__():
    router.message.outer_middleware(CacheUserMessagesMiddleware())
    router.message.middleware(CacheBotMessagesMiddleware())

    # Notes
    router.message.register(AISaveNote, *AISaveNote.filters())

    # AI Status
    router.message.register(EnableAI, *EnableAI.filters())
    router.message.register(AIStatus, *AIStatus.filters())

    # AI Context reset
    router.message.register(AIContextReset, *AIContextReset.filters())

    # AI mode
    # router.message.register(AiGenerateMode, *AiGenerateMode.filters())

    # AI translate
    router.message.register(AiTranslate, *AiTranslate.filters(), flags={"args": text_or_reply})
    router.message.outer_middleware(AiAutoTranslateMiddleware())

    # AI Auto translate
    router.message.register(ControlAIAutotrans, *ControlAIAutotrans.filters())
    router.message.register(AIAutotransStatus, *AIAutotransStatus.filters())

    # Trigger AI
    router.message.register(AiReplyHandler, *AiReplyHandler.filters())

    router.message.register(AiPmInitialize, *AiPmInitialize.filters())
    router.message.register(AiPmStop, *AiPmStop.filters())

    router.message.register(AiPmHandle, *AiPmHandle.filters())

    router.message.register(AiCmd, *AiCmd.filters())
