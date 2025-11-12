from __future__ import annotations

from typing import BinaryIO, Optional

from aiogram.types import Message

from sophie_bot.services.bot import bot


async def extract_message_content(message: Message) -> tuple[str, Optional[bytes]]:
    """
    Extract text and image content from a message for AI processing.

    Supports:
    - Text messages (text or caption)
    - Photos
    - Videos (thumbnail)
    - Stickers (static, animated, or video)

    Returns:
        tuple[str, Optional[bytes]]: Message text and optional image binary data
    """
    # Extract text content
    text_content = message.text or message.caption or ""

    # Extract image content
    image_data: Optional[bytes] = None

    if message.photo:
        # Use the largest photo size
        image_file_id = message.photo[-1].file_id
        downloaded_image: Optional[BinaryIO] = await bot.download(image_file_id)
        if downloaded_image:
            image_data = downloaded_image.read()

    elif message.video and message.video.thumbnail:
        # Use video thumbnail
        image_file_id = message.video.thumbnail.file_id
        downloaded_image = await bot.download(image_file_id)
        if downloaded_image:
            image_data = downloaded_image.read()

    elif message.animation and message.animation.thumbnail:
        # Use animation thumbnail
        image_file_id = message.animation.thumbnail.file_id
        downloaded_image = await bot.download(image_file_id)
        if downloaded_image:
            image_data = downloaded_image.read()

    elif message.sticker:
        # Handle animated/video stickers with thumbnail
        if (message.sticker.is_animated or message.sticker.is_video) and message.sticker.thumbnail:
            image_file_id = message.sticker.thumbnail.file_id
        else:
            # Static sticker
            image_file_id = message.sticker.file_id

        downloaded_image = await bot.download(image_file_id)
        if downloaded_image:
            image_data = downloaded_image.read()

    return text_content, image_data
