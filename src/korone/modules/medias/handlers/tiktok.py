from __future__ import annotations

from korone.modules.medias.utils.platforms import TikTokProvider

from .base import BaseMediaHandler


class TikTokMediaHandler(BaseMediaHandler):
    PROVIDER = TikTokProvider
    DEFAULT_AUTHOR_NAME = "TikTok"
    DEFAULT_AUTHOR_HANDLE = "tiktok"
