# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.filters.callback_data import CallbackData


class PMMenuCallback(CallbackData, prefix="pm_menu"):
    menu: str


class LangMenuCallback(CallbackData, prefix="lang"):
    menu: str


class SetLangCallback(CallbackData, prefix="setlang"):
    lang: str
