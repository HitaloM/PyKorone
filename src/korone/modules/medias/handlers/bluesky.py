from __future__ import annotations

from korone.modules.medias.utils.platforms import BlueskyProvider

from .base import BaseMediaHandler


class BlueskyMediaHandler(BaseMediaHandler):
    PROVIDER = BlueskyProvider
    DEFAULT_AUTHOR_NAME = "Bluesky"
    DEFAULT_AUTHOR_HANDLE = "bsky"
