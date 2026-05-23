from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import LangMenuCallback as LangMenuCallback
from .callbacks import SetLangCallback as SetLangCallback
from .handlers.apply import ApplyLanguageHandler
from .handlers.info import LanguageInfoCallbackHandler, LanguageInfoHandler
from .handlers.select import LanguageSelectCallbackHandler, LanguageSelectHandler, LanguageSelectPMHandler
from .stats import language_stats

router = Router(name="language")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Language"),
        icon="🌎",
        summary=l_("Language preferences and localization"),
        description=LazyProxy(lambda: Doc(l_("Check and change the bot language for private chats or groups."))),
    ),
    router=router,
    handlers=(
        LanguageInfoHandler,
        LanguageSelectHandler,
        LanguageInfoCallbackHandler,
        LanguageSelectCallbackHandler,
        LanguageSelectPMHandler,
        ApplyLanguageHandler,
    ),
    stats=language_stats,
)
