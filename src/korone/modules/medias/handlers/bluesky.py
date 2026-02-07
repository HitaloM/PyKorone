from __future__ import annotations

from korone.modules.medias.handlers.base import BaseMediaHandler
from korone.modules.medias.utils.bluesky import BlueskyProvider


class BlueskyMediaHandler(BaseMediaHandler):
    PROVIDER = BlueskyProvider
    DEFAULT_AUTHOR_NAME = "Bluesky"
    DEFAULT_AUTHOR_HANDLE = "bsky"
