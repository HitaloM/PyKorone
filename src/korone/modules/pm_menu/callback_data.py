# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.filters.callback_data import CallbackData


class LangMenuCallback(CallbackData, prefix="lang"):
    menu: str


class PMMenuCallback(CallbackData, prefix="pm_menu"):
    menu: str


class GetHelpCallback(CallbackData, prefix="gethelp"):
    module: str


class PrivacyCallback(CallbackData, prefix="privacy"):
    section: str
