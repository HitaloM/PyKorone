from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired, TypedDict, Unpack, cast

from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from korone.utils.exception import KoroneError
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.client.default import Default
    from aiogram.types import (
        InlineKeyboardMarkup,
        LinkPreviewOptions,
        MessageEntity,
        ReplyMarkupUnion,
        SuggestedPostParameters,
    )
    from stfu_tg.doc import Element


class EditTextKwargs(TypedDict, total=False):
    parse_mode: NotRequired[str | Default | None]
    entities: NotRequired[list[MessageEntity] | None]
    link_preview_options: NotRequired[LinkPreviewOptions | Default | None]
    reply_markup: NotRequired[InlineKeyboardMarkup | None]
    disable_web_page_preview: NotRequired[bool | Default | None]


class ReplyKwargs(TypedDict, total=False):
    direct_messages_topic_id: NotRequired[int | None]
    parse_mode: NotRequired[str | Default | None]
    entities: NotRequired[list[MessageEntity] | None]
    link_preview_options: NotRequired[LinkPreviewOptions | Default | None]
    disable_notification: NotRequired[bool | None]
    protect_content: NotRequired[bool | Default | None]
    allow_paid_broadcast: NotRequired[bool | None]
    message_effect_id: NotRequired[str | None]
    suggested_post_parameters: NotRequired[SuggestedPostParameters | None]
    reply_markup: NotRequired[ReplyMarkupUnion | None]
    allow_sending_without_reply: NotRequired[bool | None]
    disable_web_page_preview: NotRequired[bool | Default | None]


class ReplyOrEditKwargs(EditTextKwargs, ReplyKwargs, total=False):
    pass


async def reply_or_edit(
    event: Message | CallbackQuery, text: Element | str, **kwargs: Unpack[ReplyOrEditKwargs]
) -> Message | bool:
    if isinstance(event, CallbackQuery) and event.message:
        if isinstance(event.message, InaccessibleMessage):
            raise KoroneError(_("The message is inaccessible. Please write the command again"))

        edit_kwargs = cast("EditTextKwargs", kwargs)
        return await event.message.edit_text(str(text), **edit_kwargs)
    if isinstance(event, Message):
        reply_kwargs = cast("ReplyKwargs", kwargs)
        return await event.reply(str(text), **reply_kwargs)
    msg = "answer: Wrong event type"
    raise ValueError(msg)
