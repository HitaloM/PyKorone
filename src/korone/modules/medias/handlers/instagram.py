from __future__ import annotations

from korone.modules.medias.handlers.base import BaseMediaHandler
from korone.modules.medias.utils.instagram import InstagramProvider


class InstagramMediaHandler(BaseMediaHandler):
    PROVIDER = InstagramProvider
    DEFAULT_AUTHOR_NAME = "Instagram"
    DEFAULT_AUTHOR_HANDLE = "instagram"
