# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.filters.callback_data import CallbackData


class GetIPCallback(CallbackData, prefix="ipinfo", sep="_"):
    ip: str
