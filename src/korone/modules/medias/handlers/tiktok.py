from __future__ import annotations

from korone.modules.medias.handlers.base import BaseMediaHandler
from korone.modules.medias.utils.tiktok import TikTokProvider


class TikTokMediaHandler(BaseMediaHandler):
    PROVIDER = TikTokProvider
    DEFAULT_AUTHOR_NAME = "TikTok"
    DEFAULT_AUTHOR_HANDLE = "tiktok"
