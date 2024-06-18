from stfu_tg.base import Core


class SophieException(Exception):
    """Base class for all exceptions"""

    def __init__(self, *docs: str | Core):
        self.docs = docs
