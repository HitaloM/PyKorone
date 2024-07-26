from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sophie_bot.db.models.notes import Button, ButtonAction


def unparse_button(button: Button) -> InlineKeyboardButton:
    if button.action == ButtonAction.url:
        return InlineKeyboardButton(text=button.text, url=button.data)

    return NotImplemented


def unparse_buttons(buttons: list[list[Button]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=list(map(lambda row: list(map(unparse_button, row)), buttons)))
