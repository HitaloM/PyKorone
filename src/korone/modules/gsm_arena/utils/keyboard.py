from typing import TYPE_CHECKING

from korone.modules.gsm_arena.callbacks import DevicePageCallback, GetDeviceCallback
from korone.modules.utils_.pagination import Pagination

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup

    from .types import PhoneSearchResult


def create_pagination_layout(
    devices: list[PhoneSearchResult], query: str, page: int, user_id: int, items_per_page: int = 8
) -> InlineKeyboardMarkup:
    pagination = Pagination(
        objects=devices,
        page_data=lambda page_num: DevicePageCallback(device=query, page=page_num, user_id=user_id).pack(),
        item_data=lambda device, _: GetDeviceCallback(device=device.url, user_id=user_id).pack(),
        item_title=lambda device, _: device.name,
    )

    return pagination.create(page=page, lines=items_per_page, columns=1)
