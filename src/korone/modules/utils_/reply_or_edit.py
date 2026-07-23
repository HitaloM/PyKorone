from typing import TYPE_CHECKING, Any, cast

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from korone.utils.exception import KoroneError

if TYPE_CHECKING:
    from stfu_tg.doc import Element


def _is_message_not_modified_error(exc: TelegramBadRequest) -> bool:
    return "message is not modified" in exc.message.casefold()


async def edit_message_text(message: Message, text: Element | str, **kwargs: object) -> Message | bool:
    edit_kwargs = cast("dict[str, Any]", kwargs)
    if message.ephemeral_message_id is not None:
        if "parse_mode" not in edit_kwargs and "entities" not in edit_kwargs:
            edit_kwargs["parse_mode"] = ParseMode.HTML
        return await message.edit_ephemeral_text(str(text), **edit_kwargs)
    return await message.edit_text(str(text), **edit_kwargs)


async def reply_or_edit(event: Message | CallbackQuery, text: Element | str, **kwargs: object) -> Message | bool:
    if isinstance(event, CallbackQuery) and event.message:
        if isinstance(event.message, InaccessibleMessage):
            raise KoroneError.inaccessible_message()

        try:
            return await edit_message_text(event.message, text, **kwargs)
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
