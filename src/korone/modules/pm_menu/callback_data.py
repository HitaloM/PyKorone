# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.callback_data import CallbackData


class PMMenuCallback(CallbackData, prefix="pm_menu"):
    menu: str


class GetHelpCallback(CallbackData, prefix="gethelp"):
    module: str
