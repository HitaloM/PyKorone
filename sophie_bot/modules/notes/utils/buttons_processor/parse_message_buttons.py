from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sophie_bot.db.models.notes import Button, ButtonAction


class UnknownMessageButtonTypeError(Exception):
    pass


def parse_message_button(button: InlineKeyboardButton) -> Optional[Button]:

    if button.url:
        action = ButtonAction.url
        data = button.url
    else:
        raise UnknownMessageButtonTypeError(button)

    return Button(
        text=button.text,
        action=action,
        data=data,
    )


def parse_message_buttons_row(row: list[InlineKeyboardButton]) -> list[Button]:
    try:
        return list(filter(None, map(parse_message_button, row)))
    except UnknownMessageButtonTypeError:
        return []


def parse_message_buttons(reply_markup: InlineKeyboardMarkup) -> list[list[Button]]:
    return [parsed_row for parsed_row in map(parse_message_buttons_row, reply_markup.inline_keyboard) if parsed_row]
