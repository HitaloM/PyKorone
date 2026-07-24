from korone.modules.medias.utils.platforms import ExampleProvider

from .base import BaseMediaHandler


class ExampleMediaHandler(BaseMediaHandler):
    PROVIDER = ExampleProvider
    DEFAULT_AUTHOR_NAME = "Example"
    DEFAULT_AUTHOR_HANDLE = "example"
