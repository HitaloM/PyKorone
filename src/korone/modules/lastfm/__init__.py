from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.album import LastFMAlbumHandler
from .handlers.artist import LastFMArtistHandler
from .handlers.collage import LastFMCollageHandler
from .handlers.compat import LastFMCompatHandler
from .handlers.now import LastFMNowHandler
from .handlers.recent import LastFMRecentHandler
from .handlers.set import LastFMSetHandler, LastFMSetReplyHandler
from .handlers.top import LastFMTopHandler
from .handlers.user import LastFMUserHandler

router = Router(name="lastfm")

__module_name__ = l_("Last.fm")
__module_emoji__ = "🎵"
__module_description__ = l_("Last.fm scrobble statistics")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Shows your Last.fm stats, now playing, and top music charts."),
        l_("Includes collage generation and compatibility checks."),
    )
)

__handlers__ = (
    LastFMSetHandler,
    LastFMSetReplyHandler,
    LastFMNowHandler,
    LastFMRecentHandler,
    LastFMTopHandler,
    LastFMAlbumHandler,
    LastFMArtistHandler,
    LastFMUserHandler,
    LastFMCompatHandler,
    LastFMCollageHandler,
)
