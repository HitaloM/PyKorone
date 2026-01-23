from stfu_tg.doc import Element


class KoroneException(Exception):
    def __init__(self, *docs: str | Element):
        self.docs = docs
