import math
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.gsm_arena.callbacks import DevicePageCallback, GetDeviceCallback

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup

    from .types import PhoneSearchResult


def create_pagination_layout(
    devices: list[PhoneSearchResult], query: str, page: int, *, items_per_page: int = 8, columns: int = 1
) -> InlineKeyboardMarkup:
    total_pages = max(1, math.ceil(len(devices) / items_per_page))
    current_page = max(1, min(page, total_pages))

    start = (current_page - 1) * items_per_page
    end = start + items_per_page

    builder = InlineKeyboardBuilder()

    for device in devices[start:end]:
        builder.button(text=device.name, callback_data=GetDeviceCallback(device=device.url).pack())

    if columns > 0:
        builder.adjust(columns)

    nav_buttons: list[InlineKeyboardButton] = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=DevicePageCallback(device=query, page=current_page - 1).pack())
        )
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=DevicePageCallback(device=query, page=current_page + 1).pack())
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()
