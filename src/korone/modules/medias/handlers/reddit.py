from __future__ import annotations

from korone.modules.medias.handlers.base import BaseMediaHandler
from korone.modules.medias.utils.reddit import RedditProvider


class RedditMediaHandler(BaseMediaHandler):
    PROVIDER = RedditProvider
    DEFAULT_AUTHOR_NAME = "Reddit"
    DEFAULT_AUTHOR_HANDLE = "reddit"
