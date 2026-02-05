from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from korone.utils.exception import KoroneError
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
    from stfu_tg.doc import Element


async def reply_or_edit(
    event: Message | CallbackQuery,
    text: Element | str,
    **kwargs: dict[str, Any] | InlineKeyboardMarkup | ReplyKeyboardMarkup,
) -> Message | bool:
    if isinstance(event, CallbackQuery) and event.message:
        if isinstance(event.message, InaccessibleMessage):
            raise KoroneError(_("The message is inaccessible. Please write the command again"))

        return await event.message.edit_text(str(text), **cast("Any", kwargs))
    if isinstance(event, Message):
        return await event.reply(str(text), **cast("Any", kwargs))
    msg = "answer: Wrong event type"
    raise ValueError(msg)
