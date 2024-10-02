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
from aiogram.types import Message
from stfu_tg.doc import Element

from sophie_bot import bot
from sophie_bot.db.models.notes import Saveable, SaveableParseMode
from sophie_bot.modules.legacy_modules.modules.notes import get_note
from sophie_bot.modules.notes.utils.legacy_notes import legacy_button_parser
from sophie_bot.modules.notes.utils.parse import SUPPORTS_TEXT

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


async def send_saveable(
    message: Message,
    send_to: int,
    saveable: Saveable,
    reply_to: Optional[int] = None,
    title: Optional[Element] = None,
    raw: Optional[bool] = False,
):
    # Legacy note
    if saveable.parse_mode != SaveableParseMode.html:
        compatible_db_item = saveable.model_dump()
        compatible_db_item["parse_mode"] = (
            saveable.parse_mode.value if saveable.parse_mode else SaveableParseMode.markdown
        )
        return await get_note(message, db_item=compatible_db_item, rpl_id=reply_to, noformat=raw)

    text = str(title) + "\n" if title else ""
    text += saveable.text or ""

    # Extract buttons
    text, inline_markup = legacy_button_parser(message.chat.id, text, aio=True)

    # inline_markup = unparse_buttons(saveable.buttons)

    # Text processing
    if len(text) > 4090:
        text = f"{text[:4087]}..."

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
        kwargs["reply_to_message"] = reply_to

    return await SEND_METHOD[content_type](**kwargs).emit(bot)  # type: ignore
