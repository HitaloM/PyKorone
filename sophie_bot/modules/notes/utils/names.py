from typing import Sequence

from stfu_tg import Code, HList


def format_notes_aliases(names: Sequence[str]) -> HList:
    return HList(*(Code(f"#{name}") for name in names))
