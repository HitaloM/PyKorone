from __future__ import annotations

from typing import TYPE_CHECKING

from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from stfu_tg.doc import Element


type DocElement = str | Element


class KoroneError(Exception):
    __slots__ = ("docs",)

    def __init__(self, *docs: DocElement) -> None:
        normalized_docs = tuple(docs)
        super().__init__(*normalized_docs)
        self.docs: tuple[DocElement, ...] = normalized_docs

    @classmethod
    def inaccessible_message(cls) -> KoroneError:
        return cls(_("The message is inaccessible. Please write the command again"))

    @classmethod
    def user_context_unavailable(cls) -> KoroneError:
        return cls(_("Could not identify the user that triggered this action. Please try again."))

    @classmethod
    def user_not_found(cls) -> KoroneError:
        return cls(_("Could not identify user. Reply to a message or provide a valid user."))
