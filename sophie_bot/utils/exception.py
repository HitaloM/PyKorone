from stfu_tg.doc import Element


class SophieException(Exception):
    """Base class for all exceptions"""

    def __init__(self, *docs: str | Element):
        self.docs = docs
