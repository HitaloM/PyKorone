from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stfu_tg.doc import Element


class KoroneError(Exception):
    def __init__(self, *docs: str | Element) -> None:
        self.docs = docs
