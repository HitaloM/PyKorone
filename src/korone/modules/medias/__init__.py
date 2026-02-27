from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.bluesky import BlueskyMediaHandler
from .handlers.instagram import InstagramMediaHandler
from .handlers.reddit import RedditMediaHandler
from .handlers.status import MediaAutoDownloadStatus
from .handlers.tiktok import TikTokMediaHandler
from .handlers.twitter import TwitterMediaHandler

router = Router(name="medias")

__module_name__ = l_("Medias")
__module_emoji__ = "🖼️"
__module_description__ = l_("Automatic media downloads from supported links")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Fetch media when supported links are posted in group chats."),
        l_("Currently supported platforms: Twitter, Bluesky, Instagram, Reddit, and TikTok."),
    )
)

__handlers__ = (
    MediaAutoDownloadStatus,
    TwitterMediaHandler,
    BlueskyMediaHandler,
    InstagramMediaHandler,
    RedditMediaHandler,
    TikTokMediaHandler,
)
