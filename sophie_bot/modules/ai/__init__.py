from aiogram import Router
from stfu_tg import Doc

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsOP
from sophie_bot.modules.ai.handlers.ai_cmd import AiCmd
from sophie_bot.modules.ai.handlers.ai_moderator_setting import AIModerator
from sophie_bot.modules.ai.handlers.aiprovider import (
    AIProviderSelectCallback,
    AIProviderSetting,
    AIProviderSettingAlt,
)
from sophie_bot.modules.ai.handlers.aisave import AISaveNote
from sophie_bot.modules.ai.handlers.autotranslate_setting import (
    AIAutotrans,
)
from sophie_bot.modules.ai.handlers.enable_setting import EnableAI
from sophie_bot.modules.ai.handlers.filter import get_filter
from sophie_bot.modules.ai.handlers.op_stats import op_ai_stats_handler
from sophie_bot.modules.ai.handlers.playground import (
    AIPlaygroundCmd,
    AIPlaygroundModelSelectCallback,
)
from sophie_bot.modules.ai.handlers.pm import AiPmHandle, AiPmInitialize, AiPmStop
from sophie_bot.modules.ai.handlers.reply import AiReplyHandler
from sophie_bot.modules.ai.handlers.reset_context import AIContextReset
from sophie_bot.modules.ai.handlers.translate import AiTranslate, text_or_reply
from sophie_bot.modules.ai.magic_handlers.modern_action import AIReplyAction
from sophie_bot.modules.ai.middlewares.ai_moderator import AiModeratorMiddleware
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
    lambda: Doc(
        l_("Sophie supports quite a few ways to use AI features."),
        l_("From a simple chat-bot, to the automatic translator. Have fun."),
        " ",
        AI_POLICY,
        l_("Please note that you can make a limited amount of AI requests per day."),
    )
)

__filters__ = get_filter()
__modern_actions__ = (AIReplyAction,)
__handlers__ = (
    EnableAI,
    AIModerator,
    AIAutotrans,
    AIProviderSetting,
    AIProviderSettingAlt,
    AIProviderSelectCallback,
    AIPlaygroundCmd,
    AIPlaygroundModelSelectCallback,
    AiPmInitialize,
)


async def __pre_setup__():
    router.message.outer_middleware(CacheUserMessagesMiddleware())
    router.message.middleware(CacheBotMessagesMiddleware())

    # Notes
    router.message.register(AISaveNote, *AISaveNote.filters())

    # AI Moderator
    router.message.outer_middleware(AiModeratorMiddleware())

    # AI Context reset
    router.message.register(AIContextReset, *AIContextReset.filters())
    router.message.register(AIContextReset, *AIContextReset.filters_alt())

    # AI mode
    # router.message.register(AiGenerateMode, *AiGenerateMode.filters())

    # AI translate
    router.message.register(AiTranslate, *AiTranslate.filters(), flags={"args": text_or_reply})
    router.message.outer_middleware(AiAutoTranslateMiddleware())

    # Trigger AI
    router.message.register(AiReplyHandler, *AiReplyHandler.filters())

    router.message.register(AiPmStop, *AiPmStop.filters())

    router.message.register(AiPmHandle, *AiPmHandle.filters())

    router.message.register(AiCmd, *AiCmd.filters())

    # Operator-only: overall AI usage stats
    router.message.register(op_ai_stats_handler, CMDFilter("op_aistats"), IsOP(True))
