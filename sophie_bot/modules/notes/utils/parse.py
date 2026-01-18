from __future__ import annotations

from typing import Optional

from aiogram.enums import ContentType
from aiogram.types import Message
from stfu_tg import Section

from sophie_bot.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from sophie_bot.db.models.notes import CURRENT_SAVEABLE_VERSION, NoteFile, Saveable
from sophie_bot.db.models.notes_buttons import Button
from sophie_bot.modules.notes.utils.buttons_processor.buttons import ButtonsList, parse_message_buttons
from sophie_bot.modules.notes.utils.buttons_processor.list_from_message import parse_buttons_list_from_message
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _

PARSABLE_CONTENT_TYPES: tuple[ContentType, ...] = (
    ContentType.AUDIO,
    ContentType.ANIMATION,
    ContentType.DOCUMENT,
    ContentType.PHOTO,  # LIST??
    ContentType.STICKER,
    ContentType.VIDEO,
    ContentType.VIDEO_NOTE,
    ContentType.VOICE,
    # ContentType.CONTACT,
    # ContentType.LOCATION,
    # ContentType.POLL,
    # ContentType.DICE
)
CONTENT_TYPES_WITH_FILE_ID: tuple[ContentType, ...] = (
    ContentType.AUDIO,
    ContentType.ANIMATION,
    ContentType.DOCUMENT,
    ContentType.PHOTO,
    ContentType.STICKER,
    ContentType.VIDEO,
    ContentType.VIDEO_NOTE,
    ContentType.VOICE,
)

SUPPORTS_CAPTION: tuple[ContentType, ...] = (
    ContentType.AUDIO,
    ContentType.ANIMATION,
    ContentType.DOCUMENT,
    ContentType.PHOTO,
)


def extract_file_info(message: Message) -> Optional[NoteFile]:
    if message.content_type not in PARSABLE_CONTENT_TYPES:
        return None

    # Get file ID from the parsable fields
    attr = getattr(message, message.content_type, None)

    if not attr:
        return None

    # Photos are lists
    if isinstance(attr, list):
        attr = attr[-1]

    file_id: Optional[str] = getattr(attr, "file_id", None)
    return NoteFile(id=file_id, type=ContentType(message.content_type)) if file_id else None


def parse_reply_message(message: Message) -> tuple[str, Optional[NoteFile], list[list[Button]]]:
    if message.content_type not in (*PARSABLE_CONTENT_TYPES, ContentType.TEXT):
        raise SophieException(
            Section(
                _("Please check the notes documentation for the list of the allowed content types."),
                title=_("Reply message content is not parsable as the note."),
            )
        )

    reply_markup = getattr(message, "reply_markup", None)
    buttons = parse_message_buttons(reply_markup) if reply_markup else []

    return message.html_text, extract_file_info(message), buttons


async def parse_saveable(
    message: Message, text: Optional[str], allow_reply_message=True, buttons: ButtonsList | None = None, offset: int = 0
) -> Saveable:
    """Parses the given message and returns common note props to save."""
    # TODO: Make its own exception for notes saving
    note_text = text
    replied_buttons = []

    if allow_reply_message and message.reply_to_message and not message.reply_to_message.forum_topic_created:
        replied_message_text, file_data, replied_buttons = parse_reply_message(message.reply_to_message)

        if replied_message_text and note_text:
            note_text = f"{replied_message_text}\n{note_text}"
        elif replied_message_text:
            note_text = replied_message_text

    else:
        file_data = extract_file_info(message)

    # If not specifically added
    if buttons is None:
        buttons = ButtonsList()

    # Parse buttons (only when there's text to parse; file-only notes are allowed)
    if note_text and buttons is None:
        note_text, buttons = await parse_buttons_list_from_message(message, note_text, offset=offset)

    buttons.extend(replied_buttons)

    # TODO: Length of the message with or without HTML entities??
    if len(note_text or "") > TELEGRAM_MESSAGE_LENGTH_LIMIT:
        raise SophieException(
            Section(
                _("The maximum length of the note is {limit} characters.").format(limit=TELEGRAM_MESSAGE_LENGTH_LIMIT),
                _("Please try to reduce the length of the note."),
                title=_("Note is too long."),
            )
        )

    return Saveable(text=note_text, file=file_data, buttons=buttons, version=CURRENT_SAVEABLE_VERSION)
