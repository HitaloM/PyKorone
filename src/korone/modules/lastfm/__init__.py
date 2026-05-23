from aiogram import Router
from aiogram.utils.chat_action import ChatActionMiddleware
from stfu_tg import Doc

from korone.modules.metadata import ModuleExport, ModuleManifest, ModulePackage, ModuleScripts
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .export import export_lastfm
from .handlers.album import LastFMAlbumCallbackHandler, LastFMAlbumHandler
from .handlers.artist import LastFMArtistCallbackHandler, LastFMArtistHandler
from .handlers.collage import LastFMCollageCallbackHandler, LastFMCollageHandler
from .handlers.compat import LastFMCompatHandler
from .handlers.lfm import LastFMStatusCallbackHandler, LastFMStatusHandler
from .handlers.set import LastFMSetHandler, LastFMSetReplyHandler, LastFMSetStartHandler
from .stats import lastfm_stats

router = Router(name="lastfm")


def pre_setup() -> None:
    router.message.middleware(ChatActionMiddleware())


manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Last.fm"),
        icon="🎵",
        summary=l_("Last.fm now-playing and profile tools"),
        description=LazyProxy(
            lambda: Doc(l_("Show current scrobbles and fetch album, artist, compatibility, and collage views."))
        ),
    ),
    router=router,
    handlers=(
        LastFMSetHandler,
        LastFMSetStartHandler,
        LastFMSetReplyHandler,
        LastFMStatusHandler,
        LastFMStatusCallbackHandler,
        LastFMAlbumHandler,
        LastFMAlbumCallbackHandler,
        LastFMArtistHandler,
        LastFMArtistCallbackHandler,
        LastFMCompatHandler,
        LastFMCollageHandler,
        LastFMCollageCallbackHandler,
    ),
    scripts=ModuleScripts(pre_setup=pre_setup),
    stats=lastfm_stats,
    export=ModuleExport(export_lastfm, private_only=True),
)
