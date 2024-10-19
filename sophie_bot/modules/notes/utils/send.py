from typing import Optional, Type

from aiogram.enums import ContentType
from aiogram.methods import (
    SendAnimation,
    SendAudio,
    SendContact,
    SendDice,
    SendDocument,
    SendGame,
    SendLocation,
    SendMessage,
    SendPhoto,
    SendPoll,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVoice,
    TelegramMethod,
)
from aiogram.types import Message, ReplyParameters
from stfu_tg import HList

from sophie_bot import bot
from sophie_bot.db.models.notes import Saveable, SaveableParseMode
from sophie_bot.modules.notes.utils.legacy_notes import (
    legacy_button_parser,
    send_note,
    t_unparse_note_item,
)
from sophie_bot.modules.notes.utils.parse import SUPPORTS_TEXT
from sophie_bot.modules.notes.utils.text import parse_vars_chat, parse_vars_user
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _

SEND_METHOD: dict[ContentType, Type[TelegramMethod[Message]]] = {
    ContentType.TEXT: SendMessage,
    ContentType.AUDIO: SendAudio,
    ContentType.ANIMATION: SendAnimation,
    ContentType.DOCUMENT: SendDocument,
    ContentType.GAME: SendGame,
    ContentType.PHOTO: SendPhoto,
    ContentType.STICKER: SendSticker,
    ContentType.VIDEO: SendVideo,
    ContentType.VIDEO_NOTE: SendVideo,
    ContentType.VOICE: SendVoice,
    ContentType.CONTACT: SendContact,
    ContentType.VENUE: SendVenue,
    ContentType.LOCATION: SendLocation,
    ContentType.POLL: SendPoll,
    ContentType.DICE: SendDice,
}


async def send_saveable_legacy(
    message: Message,
    saveable: Saveable,
    send_to: int,
    reply_to: Optional[int] = None,
    legacy_title: Optional[str] = None,
    raw: Optional[bool] = False,
):
    compatible_db_item = saveable.model_dump()
    compatible_db_item["parse_mode"] = saveable.parse_mode.value if saveable.parse_mode else SaveableParseMode.markdown
    text, kwargs = await t_unparse_note_item(
        message, compatible_db_item, send_to, noformat=raw, event=message, user=message.from_user
    )

    if legacy_title:
        text = f"{legacy_title}\n{text}"

    kwargs["reply_to"] = reply_to

    await send_note(send_to, text, **kwargs)


async def send_saveable(
    message: Message,
    send_to: int,
    saveable: Saveable,
    reply_to: Optional[int] = None,
    title: Optional[HList] = None,
    legacy_title: Optional[str] = None,
    raw: Optional[bool] = False,
):
    text = str(title) + "\n" if title else ""

    # Legacy note
    if saveable.parse_mode != SaveableParseMode.html and saveable.file:
        return await send_saveable_legacy(
            message=message,
            saveable=saveable,
            send_to=send_to,
            reply_to=reply_to,
            legacy_title=legacy_title,
            raw=raw,
        )
    elif saveable.parse_mode != SaveableParseMode.html:
        text += legacy_markdown_to_html(saveable.text or "")
    else:
        text += saveable.text or ""

    # Extract buttons and process text
    inline_markup = None
    if not raw:
        text, inline_markup = legacy_button_parser(message.chat.id, text, aio=True)
        text = parse_vars_chat(text, message)
        text = parse_vars_user(text, message, message.from_user)

    # inline_markup = unparse_buttons(saveable.buttons)

    if len(text) > 4090:
        raise SophieException(_("The text is too long"))

    # TODO: Media groups
    # TODO: Multi messages

    content_type = saveable.file.type if saveable.file else ContentType.TEXT

    kwargs = {
        "chat_id": send_to,
        "text": text,
    }

    if content_type in SUPPORTS_TEXT:
        kwargs["text"] = text
        kwargs["reply_markup"] = inline_markup
    elif not saveable.file:
        raise ValueError(f"Unsupported content type: {content_type}")
    else:
        kwargs[content_type] = saveable.file.id

    if reply_to:
        kwargs["reply_parameters"] = ReplyParameters(message_id=reply_to)

    def to_try(**cb_kwargs):
        return SEND_METHOD[content_type](**cb_kwargs).emit(bot)  # type: ignore

    async def reply_not_found():
        if "reply_parameters" in kwargs:
            del kwargs["reply_parameters"]
        return await to_try(**kwargs)

    return await common_try(to_try=to_try(**kwargs), reply_not_found=reply_not_found)
