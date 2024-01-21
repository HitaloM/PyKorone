# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.callback_data import CallbackData


class LangMenuCallback(CallbackData, prefix="lang"):
    menu: str


class SetLangCallback(CallbackData, prefix="setlang"):
    lang: str
