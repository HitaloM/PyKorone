from __future__ import annotations

from korone.modules.medias.utils.platforms import InstagramProvider

from .base import BaseMediaHandler


class InstagramMediaHandler(BaseMediaHandler):
    PROVIDER = InstagramProvider
    DEFAULT_AUTHOR_NAME = "Instagram"
    DEFAULT_AUTHOR_HANDLE = "instagram"
