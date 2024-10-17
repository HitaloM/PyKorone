from typing import Optional

from aiogram.enums import ContentType
from aiogram.types import Message
from stfu_tg import Section

from sophie_bot.db.models.notes import Button, NoteFile, Saveable
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

SUPPORTS_TEXT: tuple[ContentType, ...] = (
    ContentType.TEXT,
    ContentType.AUDIO,
    ContentType.ANIMATION,
    ContentType.DOCUMENT,
)

MESSAGE_LENGTH_LIMIT = 4096


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


def parse_reply_message(message: Message) -> tuple[Optional[str], Optional[NoteFile], list[list[Button]]]:
    if message.content_type not in (*PARSABLE_CONTENT_TYPES, ContentType.TEXT):
        raise SophieException(
            Section(
                _("Please check the notes documentation for the list of the allowed content types."),
                title=_("Reply message content is not parsable as the note."),
            )
        )

    # buttons = parse_message_buttons(message.reply_markup) if message.reply_markup else []
    buttons: list = []

    return message.html_text, extract_file_info(message), buttons


async def parse_saveable(message: Message, text: Optional[str], allow_reply_message=True) -> Saveable:
    """Parses the given message and returns common note props to save."""
    # TODO: Make its own exception for notes saving
    note_text = text
    buttons = []

    if message.reply_to_message and allow_reply_message:
        replied_message_text, file_data, replied_buttons = parse_reply_message(message.reply_to_message)

        buttons.extend(replied_buttons)

        if replied_message_text and note_text:
            note_text = f"{replied_message_text}\n{note_text}"
        elif replied_message_text:
            note_text = replied_message_text

    else:
        file_data = extract_file_info(message)

    # TODO: Length of the message with or without HTML entities??
    if len(note_text or "") > MESSAGE_LENGTH_LIMIT:
        raise SophieException(
            Section(
                _("The maximum length of the note is {limit} characters.").format(limit=MESSAGE_LENGTH_LIMIT),
                _("Please try to reduce the length of the note."),
                title=_("Note is too long."),
            )
        )

    return Saveable(text=note_text, file=file_data, buttons=buttons)
