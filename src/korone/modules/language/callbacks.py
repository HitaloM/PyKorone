from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class LangMenu(StrEnum):
    Language = "language"
    Languages = "languages"


class LangMenuCallback(CallbackData, prefix="lang"):
    menu: LangMenu
    back_to_start: bool = False


class SetLangCallback(CallbackData, prefix="setlang"):
    lang: str
    back_to_start: bool = False
