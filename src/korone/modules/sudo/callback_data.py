# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.filters.callback_data import CallbackData


class UpdateCallbackData(CallbackData, prefix="updater"):
    pass


class PingCallbackData(CallbackData, prefix="ping"):
    pass
