from __future__ import annotations

from korone.modules.medias.utils.platforms import RedditProvider

from .base import BaseMediaHandler


class RedditMediaHandler(BaseMediaHandler):
    PROVIDER = RedditProvider
    DEFAULT_AUTHOR_NAME = "Reddit"
    DEFAULT_AUTHOR_HANDLE = "reddit"
