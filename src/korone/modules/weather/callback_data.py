# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hairydogm.filters.callback_data import CallbackData


class WeatherCallbackData(CallbackData, prefix="weather"):
    latitude: float | None = None
    longitude: float | None = None
    page: int | None = None
