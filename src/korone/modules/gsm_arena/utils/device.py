from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import InputRichMessage, LinkPreviewOptions, Message

from korone.modules.utils_.reply_or_edit import edit_message_rich, edit_message_text, reply_message, reply_message_rich
from korone.ui.rendering import text_kwargs
from korone.utils.telegram_errors import is_message_not_modified_error, is_message_to_edit_not_found_error

from .formatters import format_phone, format_phone_rich
from .scraper import check_phone_details

if TYPE_CHECKING:
    from korone.ui import MessageContent


@dataclass(frozen=True, slots=True)
class DevicePresentation:
    text: MessageContent
    rich_message: InputRichMessage
    preview_options: LinkPreviewOptions


async def get_device_presentation(url: str) -> DevicePresentation | None:
    if phone := await check_phone_details(url):
        return DevicePresentation(
            text=format_phone(phone),
            rich_message=format_phone_rich(phone),
            preview_options=LinkPreviewOptions(
                is_disabled=False, url=phone.picture or phone.url, prefer_large_media=True, show_above_text=True
            ),
        )
    return None


async def reply_with_device(message: Message, presentation: DevicePresentation) -> Message:
    try:
        return await reply_message_rich(message, presentation.rich_message)
    except TelegramBadRequest, TelegramNotFound:
        return await reply_message(message, presentation.text, link_preview_options=presentation.preview_options)


async def answer_with_device(message: Message, presentation: DevicePresentation) -> Message:
    try:
        return await message.answer_rich(presentation.rich_message)
    except TelegramBadRequest, TelegramNotFound:
        return await message.answer(**text_kwargs(presentation.text, link_preview_options=presentation.preview_options))


async def edit_with_device(message: Message, presentation: DevicePresentation) -> Message | bool:
    try:
        return await edit_message_rich(message, presentation.rich_message)
    except TelegramBadRequest as error:
        if is_message_not_modified_error(error) or is_message_to_edit_not_found_error(error):
            raise
    except TelegramNotFound:
        pass

    return await edit_message_text(message, presentation.text, link_preview_options=presentation.preview_options)
