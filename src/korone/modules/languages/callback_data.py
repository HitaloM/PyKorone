# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from enum import StrEnum

from hairydogm.filters.callback_data import CallbackData


class LangMenu(StrEnum):
    Language = "language"
    Languages = "languages"
    Cancel = "cancel"


class LangMenuCallback(CallbackData, prefix="lang"):
    menu: LangMenu


class SetLangCallback(CallbackData, prefix="setlang"):
    lang: str
