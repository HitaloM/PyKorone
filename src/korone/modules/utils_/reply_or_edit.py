from typing import TYPE_CHECKING, Any, cast

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from korone.modules.utils_.message import get_message
from korone.ui.rendering import text_kwargs
from korone.utils.telegram_errors import is_message_not_modified_error, is_message_to_reply_not_found_error

if TYPE_CHECKING:
    from aiogram.types import InputRichMessage

    from korone.ui import MessageContent


async def edit_message_text(message: Message, text: MessageContent, **kwargs: object) -> Message | bool:
    edit_kwargs = text_kwargs(text, **kwargs)
    if message.ephemeral_message_id is not None:
        return await message.edit_ephemeral_text(**edit_kwargs)
    return await message.edit_text(**edit_kwargs)


async def edit_message_rich(message: Message, rich_message: InputRichMessage, **kwargs: object) -> Message | bool:
    if message.ephemeral_message_id is not None:
        return await message.edit_ephemeral_text(rich_message=rich_message, **cast("dict[str, Any]", kwargs))
    return await message.edit_text(rich_message=rich_message, **cast("dict[str, Any]", kwargs))


async def reply_message(message: Message, text: MessageContent, **kwargs: object) -> Message:
    send_kwargs = text_kwargs(text, **kwargs)
    try:
        return await message.reply(**send_kwargs)
    except TelegramBadRequest as exc:
        if not is_message_to_reply_not_found_error(exc):
            raise
        return await message.answer(**send_kwargs)


async def reply_message_rich(message: Message, rich_message: InputRichMessage, **kwargs: object) -> Message:
    rich_kwargs = cast("dict[str, Any]", kwargs)
    try:
        return await message.reply_rich(rich_message, **rich_kwargs)
    except TelegramBadRequest as exc:
        if not is_message_to_reply_not_found_error(exc):
            raise
        return await message.answer_rich(rich_message, **rich_kwargs)


async def reply_or_edit(event: Message | CallbackQuery, text: MessageContent, **kwargs: object) -> Message | bool:
    if isinstance(event, CallbackQuery):
        message = get_message(event)
        try:
            return await edit_message_text(message, text, **kwargs)
        except TelegramBadRequest as exc:
            if not is_message_not_modified_error(exc):
                raise
            return message
    if isinstance(event, Message):
        return await reply_message(event, text, **kwargs)
    msg = "answer: Wrong event type"
    raise ValueError(msg)


async def reply_or_edit_rich(
    event: Message | CallbackQuery, rich_message: InputRichMessage, **kwargs: object
) -> Message | bool:
    if isinstance(event, CallbackQuery):
        message = get_message(event)
        try:
            return await edit_message_rich(message, rich_message, **kwargs)
        except TelegramBadRequest as exc:
            if not is_message_not_modified_error(exc):
                raise
            return message
    if isinstance(event, Message):
        return await reply_message_rich(event, rich_message, **kwargs)
    msg = "answer_rich: Wrong event type"
    raise ValueError(msg)
