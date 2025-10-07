# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from anyio import Path as AsyncPath
from anyio import to_thread
from hydrogram.types import Message

from korone.utils.i18n import gettext as _

from .ffmpeg import ffprobe, resize_image, resize_video


def determine_mime_type_and_suffix(media_type: str) -> tuple[str, str]:
    return {
        "video": ("video/webm", "video"),
        "animated": ("application/x-tgsticker", "animated"),
    }.get(media_type, ("image/png", ""))


def determine_media_type(message: Message) -> tuple[str | None, str | None, str | None]:
    media_type = None
    file_id = None
    extension = None

    if photo := message.reply_to_message.photo:
        media_type = "photo"
        file_id = photo.file_id
        extension = ".png"
    elif video := message.reply_to_message.video:
        media_type = "video"
        file_id = video.file_id
        extension = ".mp4"
    elif animation := message.reply_to_message.animation:
        media_type = "video"
        file_id = animation.file_id
        extension = ".mp4"
    elif document := message.reply_to_message.document:
        if document.mime_type and "image" in document.mime_type:
            media_type = "photo"
            file_id = document.file_id
            extension = ".png"
        elif document.mime_type and "video" in document.mime_type:
            media_type = "video"
            file_id = document.file_id
            extension = ".mp4"
    elif sticker := message.reply_to_message.sticker:
        if sticker.is_animated:
            media_type = "animated"
            extension = ".tgs"
        elif sticker.is_video:
            media_type = "video"
            extension = ".webm"
        else:
            media_type = "photo"
            extension = ".webp"

        file_id = sticker.file_id
    return media_type, file_id, extension


async def check_video(message: Message, file_path: str) -> bool:
    duration_str = await ffprobe(file_path)

    if not duration_str:
        await message.edit(_("Failed to get video information."))
        return False

    try:
        duration = float(duration_str)
    except (ValueError, IndexError) as e:
        await message.reply(_("Error parsing video information: {error}").format(error=str(e)))
        return False

    size = (await AsyncPath(file_path).stat()).st_size

    if duration > 3:
        await message.edit(
            _("The video is too long ({duration}s)!\nMax duration is 3 seconds.").format(
                duration=duration
            )
        )
        return False

    if size > 256000:
        await message.edit(
            _("The video is too big ({size}KB)!\nMax size is 256KB").format(size=size / 1000)
        )
        return False

    return True


async def resize_media(media_type: str, file_path: str) -> str | None:
    if media_type in {"photo", "animated"}:
        return await to_thread.run_sync(resize_image, file_path)

    return await resize_video(file_path)
