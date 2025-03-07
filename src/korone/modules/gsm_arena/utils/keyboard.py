# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import InlineKeyboardMarkup

from korone.modules.gsm_arena.callback_data import DevicePageCallback, GetDeviceCallback
from korone.utils.pagination import Pagination


def create_pagination_layout(devices: list, query: str, page: int) -> InlineKeyboardMarkup:
    layout = Pagination(
        devices,
        item_data=lambda i, _: GetDeviceCallback(device=i.url).pack(),
        item_title=lambda i, _: i.name,
        page_data=lambda pg: DevicePageCallback(device=query, page=pg).pack(),
    )
    return layout.create(page, lines=8)
