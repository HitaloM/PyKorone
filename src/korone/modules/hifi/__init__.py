from aiogram import Router
from aiogram.utils.chat_action import ChatActionMiddleware
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import HifiTrackDownloadCallback as HifiTrackDownloadCallback
from .callbacks import HifiTrackSendCallback as HifiTrackSendCallback
from .callbacks import HifiTracksPageCallback as HifiTracksPageCallback
from .handlers.list import HifiTrackListCallbackHandler
from .handlers.preview import HifiTrackPreviewCallbackHandler
from .handlers.search import HifiSearchHandler
from .handlers.send import HifiTrackDownloadCallbackHandler

router = Router(name="hifi")

__module_name__ = l_("HiFi")
__module_emoji__ = "🎧"
__module_description__ = l_("HiFi music search and delivery")
__module_info__ = LazyProxy(lambda: Doc(l_("Search tracks, preview results, and send high-quality audio files.")))

__handlers__ = (
    HifiSearchHandler,
    HifiTrackListCallbackHandler,
    HifiTrackPreviewCallbackHandler,
    HifiTrackDownloadCallbackHandler,
)


def __pre_setup__() -> None:
    router.message.middleware(ChatActionMiddleware())
