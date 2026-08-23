from aiogram import Router

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.formatting import Doc
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.media import MediaHandler
from .handlers.status import MediaAutoDownloadStatus

router = Router(name="medias")


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
    handlers=(MediaAutoDownloadStatus, MediaHandler),
)
