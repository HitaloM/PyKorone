from korone.modules.medias.utils.platforms import PinterestProvider

from .base import BaseMediaHandler


class PinterestMediaHandler(BaseMediaHandler):
    PROVIDER = PinterestProvider
    DEFAULT_AUTHOR_NAME = "Pinterest"
    DEFAULT_AUTHOR_HANDLE = "pinterest"
