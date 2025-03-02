# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from enum import StrEnum

from hairydogm.filters.callback_data import CallbackData


class PMMenu(StrEnum):
    Start = "start"
    Help = "help"
    About = "about"


class PMMenuCallback(CallbackData, prefix="pm_menu"):
    menu: PMMenu
