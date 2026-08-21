from dataclasses import dataclass

from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import InputRichMessage, LinkPreviewOptions, Message

from korone.utils.telegram_errors import is_message_not_modified_error, is_message_to_edit_not_found_error

from .formatters import format_phone, format_phone_rich
from .scraper import check_phone_details


@dataclass(frozen=True, slots=True)
class DevicePresentation:
    text: str
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
        return await message.reply_rich(presentation.rich_message)
    except TelegramBadRequest, TelegramNotFound:
        return await message.reply(text=presentation.text, link_preview_options=presentation.preview_options)


async def answer_with_device(message: Message, presentation: DevicePresentation) -> Message:
    try:
        return await message.answer_rich(presentation.rich_message)
    except TelegramBadRequest, TelegramNotFound:
        return await message.answer(text=presentation.text, link_preview_options=presentation.preview_options)


async def edit_with_device(message: Message, presentation: DevicePresentation) -> Message | bool:
    try:
        return await message.edit_text(rich_message=presentation.rich_message)
    except TelegramBadRequest as error:
        if is_message_not_modified_error(error) or is_message_to_edit_not_found_error(error):
            raise
    except TelegramNotFound:
        pass

    return await message.edit_text(text=presentation.text, link_preview_options=presentation.preview_options)
