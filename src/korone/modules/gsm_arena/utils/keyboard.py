# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import InlineKeyboardMarkup

from korone.modules.gsm_arena.callback_data import DevicePageCallback, GetDeviceCallback
from korone.utils.pagination import Pagination

from .types import PhoneSearchResult


def create_pagination_layout(
    devices: list[PhoneSearchResult],
    query: str,
    page: int,
    items_per_page: int = 8,
) -> InlineKeyboardMarkup:
    pagination = Pagination(
        objects=devices,
        page_data=lambda page_num: DevicePageCallback(device=query, page=page_num).pack(),
        item_data=lambda device, _: GetDeviceCallback(device=device.url).pack(),
        item_title=lambda device, _: device.name,
    )

    return pagination.create(page=page, lines=items_per_page, columns=1)
