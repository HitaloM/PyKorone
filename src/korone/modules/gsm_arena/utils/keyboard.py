from typing import TYPE_CHECKING

from korone.modules.gsm_arena.callbacks import DevicePageCallback, GetDeviceCallback
from korone.modules.utils_.pagination import Pagination

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup

    from .types import PhoneSearchResult


def create_pagination_layout(
    devices: list[PhoneSearchResult], token: str, page: int, user_id: int, items_per_page: int = 8
) -> InlineKeyboardMarkup:
    indexed_devices = list(enumerate(devices))

    pagination = Pagination(
        objects=indexed_devices,
        page_data=lambda page_num: DevicePageCallback(token=token, page=page_num, user_id=user_id).pack(),
        item_data=lambda item, _: GetDeviceCallback(token=token, index=item[0], user_id=user_id).pack(),
        item_title=lambda item, _: item[1].name,
    )

    return pagination.create(page=page, lines=items_per_page, columns=1)
