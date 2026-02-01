from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import LangMenuCallback as LangMenuCallback
from .callbacks import SetLangCallback as SetLangCallback
from .export import export_chat_language
from .handlers.apply import ApplyLanguageHandler
from .handlers.cancel import LanguageCancelHandler
from .handlers.info import LanguageInfoCallbackHandler, LanguageInfoHandler
from .handlers.select import LanguageSelectCallbackHandler, LanguageSelectHandler, LanguageSelectPMHandler
from .stats import language_stats

router = Router(name="language")

__module_name__ = l_("Language")
__module_emoji__ = "🌍"
__module_description__ = l_("Change the bot language")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_(
            "Customize your experience by selecting your preferred language for interacting with the bot. "
            "Choose from a variety of supported languages to make your conversations more comfortable and enjoyable."
        )
    )
)

__export__ = export_chat_language

__handlers__ = (
    LanguageInfoHandler,
    LanguageSelectHandler,
    LanguageInfoCallbackHandler,
    LanguageSelectCallbackHandler,
    LanguageSelectPMHandler,
    ApplyLanguageHandler,
    LanguageCancelHandler,
)

__stats__ = language_stats
