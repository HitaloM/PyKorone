from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from korone.utils.exception import KoroneError

if TYPE_CHECKING:
    from stfu_tg.doc import Element


def _is_message_not_modified_error(exc: TelegramBadRequest) -> bool:
    return "message is not modified" in exc.message.casefold()


async def reply_or_edit(event: Message | CallbackQuery, text: Element | str, **kwargs: object) -> Message | bool:
    if isinstance(event, CallbackQuery) and event.message:
        if isinstance(event.message, InaccessibleMessage):
            raise KoroneError.inaccessible_message()

        try:
            return await event.message.edit_text(str(text), **cast("dict[str, Any]", kwargs))
        except TelegramBadRequest as exc:
            if not _is_message_not_modified_error(exc):
                raise
            return event.message
    if isinstance(event, Message):
        try:
            return await event.reply(str(text), **cast("dict[str, Any]", kwargs))
        except TelegramBadRequest as exc:
            if "message to be replied not found" not in exc.message.lower():
                raise
            return await event.answer(str(text), **cast("dict[str, Any]", kwargs))
    msg = "answer: Wrong event type"
    raise ValueError(msg)
