from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.bluesky import BlueskyMediaHandler
from .handlers.instagram import InstagramMediaHandler
from .handlers.reddit import RedditMediaHandler
from .handlers.status import MediaAutoDownloadStatus
from .handlers.tiktok import TikTokMediaHandler
from .handlers.twitter import TwitterMediaHandler

router = Router(name="medias")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Medias"),
        icon="🖼️",
        summary=l_("Automatic media downloads from supported links"),
        description=LazyProxy(
            lambda: Doc(
                l_("Fetch media when supported links are posted in group chats."),
                l_("Currently supported platforms: Twitter, Bluesky, Instagram, Reddit, and TikTok."),
            )
        ),
    ),
    router=router,
    handlers=(
        MediaAutoDownloadStatus,
        TwitterMediaHandler,
        BlueskyMediaHandler,
        InstagramMediaHandler,
        RedditMediaHandler,
        TikTokMediaHandler,
    ),
)
