# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from enum import StrEnum

from hairydogm.filters.callback_data import CallbackData


class DelAllFiltersAction(StrEnum):
    Confim = "confirm"
    Cancel = "cancel"


class DelAllFiltersCallback(CallbackData, prefix="delallfilters"):
    action: DelAllFiltersAction
