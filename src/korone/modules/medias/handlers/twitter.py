from __future__ import annotations

from korone.modules.medias.handlers.base import BaseMediaHandler
from korone.modules.medias.utils.fxtwitter import FXTwitterProvider


class TwitterMediaHandler(BaseMediaHandler):
    PROVIDER = FXTwitterProvider
    DEFAULT_AUTHOR_NAME = "Twitter"
    DEFAULT_AUTHOR_HANDLE = "twitter"
