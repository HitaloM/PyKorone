from aiogram import Router

from korone.modules.metadata import ModuleManifest, ModulePackage, ModuleScripts
from korone.utils.formatting import Doc
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.bluesky import BlueskyMediaHandler
from .handlers.instagram import InstagramMediaHandler
from .handlers.pinterest import PinterestMediaHandler
from .handlers.reddit import RedditMediaHandler
from .handlers.status import MediaAutoDownloadStatus
from .handlers.tiktok import TikTokMediaHandler
from .handlers.twitter import TwitterMediaHandler
from .middlewares import MediaProcessingMiddleware
from .utils.processing import MediaProcessingManager

router = Router(name="medias")
processing_manager = MediaProcessingManager()


def pre_setup() -> None:
    router.message.middleware(MediaProcessingMiddleware(processing_manager))
    router.startup.register(processing_manager.start)
    router.shutdown.register(processing_manager.shutdown)


manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Medias"),
        icon="🖼️",
        summary=l_("Automatic media downloads from supported links"),
        description=LazyProxy(
            lambda: Doc(
                l_("Fetch media when supported links are posted in private or group chats."),
                l_("Currently supported platforms: Twitter, Bluesky, Instagram, Pinterest, Reddit, and TikTok."),
            )
        ),
    ),
    router=router,
    handlers=(
        MediaAutoDownloadStatus,
        TwitterMediaHandler,
        BlueskyMediaHandler,
        InstagramMediaHandler,
        PinterestMediaHandler,
        RedditMediaHandler,
        TikTokMediaHandler,
    ),
    scripts=ModuleScripts(pre_setup=pre_setup),
)
