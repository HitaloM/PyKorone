from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.bluesky import BlueskyMediaHandler
from .handlers.instagram import InstagramMediaHandler
from .handlers.reddit import RedditMediaHandler
from .handlers.status import MediaAutoDownloadStatus
from .handlers.twitter import TwitterMediaHandler

router = Router(name="medias")

__module_name__ = l_("Medias")
__module_emoji__ = "🖼️"
__module_description__ = l_("Download media from supported websites in group chats")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_(
            "Automatically fetches photos and videos from supported links posted in the group.\n\n"
            "Currently supports: Twitter, Bluesky, Instagram, Reddit."
        )
    )
)

__handlers__ = (
    MediaAutoDownloadStatus,
    TwitterMediaHandler,
    BlueskyMediaHandler,
    InstagramMediaHandler,
    RedditMediaHandler,
)
