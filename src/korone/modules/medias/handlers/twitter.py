from __future__ import annotations

from korone.modules.medias.utils.platforms import TwitterProvider

from .base import BaseMediaHandler


class TwitterMediaHandler(BaseMediaHandler):
    PROVIDER = TwitterProvider
    DEFAULT_AUTHOR_NAME = "Twitter"
    DEFAULT_AUTHOR_HANDLE = "twitter"
