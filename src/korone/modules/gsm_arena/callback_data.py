# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.callback_data import CallbackData


class GetDeviceCallback(CallbackData, prefix="gsm_query"):
    device: str


class DevicePageCallback(CallbackData, prefix="gsm_qpage"):
    device: str
    page: int
