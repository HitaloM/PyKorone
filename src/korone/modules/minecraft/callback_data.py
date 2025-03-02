# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hairydogm.filters.callback_data import CallbackData


class GetModrinthProjectCallback(CallbackData, prefix="get_modrinth"):
    project_id: str


class ModrinthPageCallback(CallbackData, prefix="modrinth_page"):
    query: str
    page: int


class ModrinthDetailsCallback(CallbackData, prefix="modrinth_details"):
    project_id: str
