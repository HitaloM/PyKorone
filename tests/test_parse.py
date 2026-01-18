from unittest.mock import AsyncMock, patch

import pytest
from aiogram.enums import ContentType
from aiogram.types import Message

from sophie_bot.db.models.notes import NoteFile
from sophie_bot.modules.notes.utils.parse import (
    extract_file_info,
    parse_reply_message,
    parse_saveable,
)
from sophie_bot.utils.exception import SophieException


@pytest.mark.asyncio
async def test_parse_saveable_with_text_only():
    message = AsyncMock(spec=Message)
    message.reply_to_message = None
    message.content_type = ContentType.TEXT

    result = await parse_saveable(message, text="This is a note.")
    assert result.text == "This is a note."
    assert result.file is None
    assert result.buttons == []


@pytest.mark.asyncio
async def test_parse_saveable_with_reply_message():
    message = AsyncMock(spec=Message)
    message.reply_to_message = AsyncMock(spec=Message)
    message.reply_to_message.forum_topic_created = False
    message.reply_to_message.html_text = "Replied message text"
    message.reply_to_message.content_type = ContentType.TEXT
    message.content_type = ContentType.TEXT

    with patch("sophie_bot.modules.notes.utils.parse.parse_reply_message") as mock_parse_reply_message:
        mock_parse_reply_message.return_value = ("Replied message text", None, [])
        result = await parse_saveable(message, text="This is a note.")
        assert result.text == "Replied message text\nThis is a note."
        assert result.file is None
        assert result.buttons == []


@pytest.mark.asyncio
async def test_parse_saveable_exceeding_length_limit():
    message = AsyncMock(spec=Message)
    message.reply_to_message = None
    message.content_type = ContentType.TEXT

    text = "A" * 1001  # Assuming TELEGRAM_MESSAGE_LENGTH_LIMIT is patched to 1000
    with patch("sophie_bot.modules.notes.utils.parse.TELEGRAM_MESSAGE_LENGTH_LIMIT", 1000):
        with pytest.raises(SophieException):
            await parse_saveable(message, text=text)


@pytest.mark.asyncio
async def test_parse_saveable_with_file_data():
    message = AsyncMock(spec=Message)
    message.reply_to_message = None
    message.content_type = ContentType.PHOTO
    message.photo = [AsyncMock(file_id="file_123")]

    with patch("sophie_bot.modules.notes.utils.parse.extract_file_info") as mock_extract_file_info:
        mock_extract_file_info.return_value = NoteFile(id="file_123", type=ContentType.PHOTO)
        result = await parse_saveable(message, text=None)
        assert result.file.id == "file_123"
        assert result.file.type == ContentType.PHOTO
        assert result.text is None
        assert result.buttons == []


def test_parse_reply_message_with_text():
    message = AsyncMock(spec=Message)
    message.content_type = ContentType.TEXT
    message.html_text = "Sample text"

    result = parse_reply_message(message)
    assert result[0] == "Sample text"
    assert result[1] is None
    assert result[2] == []


def test_parse_reply_message_with_unsupported_content_type():
    message = AsyncMock(spec=Message)
    message.content_type = ContentType.LOCATION

    with pytest.raises(SophieException):
        parse_reply_message(message)


def test_extract_file_info_with_photo():
    message = AsyncMock(spec=Message)
    message.content_type = ContentType.PHOTO
    message.photo = [AsyncMock(file_id="photo_456")]

    result = extract_file_info(message)
    assert result.id == "photo_456"
    assert result.type == ContentType.PHOTO


def test_extract_file_info_with_non_parsable_content_type():
    message = AsyncMock(spec=Message)
    message.content_type = ContentType.VIDEO

    result = extract_file_info(message)
    assert result is None
