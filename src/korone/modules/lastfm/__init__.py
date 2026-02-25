from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .export import export_lastfm
from .handlers.album import LastFMAlbumCallbackHandler, LastFMAlbumHandler
from .handlers.artist import LastFMArtistCallbackHandler, LastFMArtistHandler
from .handlers.collage import LastFMCollageCallbackHandler, LastFMCollageHandler
from .handlers.compat import LastFMCompatHandler
from .handlers.lfm import LastFMStatusCallbackHandler, LastFMStatusHandler
from .handlers.set import LastFMSetHandler, LastFMSetReplyHandler
from .stats import lastfm_stats

router = Router(name="lastfm")

__module_name__ = l_("Last.fm")
__module_emoji__ = "🎵"
__module_description__ = l_("Show your Last.fm status")
__module_info__ = LazyProxy(lambda: Doc(l_("Show your current or last played track from Last.fm.")))

__export_private_only__ = True
__export__ = export_lastfm

__handlers__ = (
    LastFMSetHandler,
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
)

__stats__ = lastfm_stats
