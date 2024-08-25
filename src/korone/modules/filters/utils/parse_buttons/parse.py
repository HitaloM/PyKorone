# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from korone.modules.filters.utils.types import Button, ButtonAction

BUTTON_URL_REGEX = re.compile(r"\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\)")


class UnknownMessageButtonTypeError(Exception):
    pass


def parse_text_buttons(text: str) -> list[list[Button]]:
    if not BUTTON_URL_REGEX.search(text):
        return []

    buttons = []
    current_row = []

    for match in BUTTON_URL_REGEX.finditer(text):
        escapes_count = sum(text[i] == "\\" for i in range(match.start() - 1, -1, -1))
        is_escaped = escapes_count % 2 != 0

        if not is_escaped:
            button = Button(
                text=match.group(1),
                action=ButtonAction.URL,
                data=match.group(2),
                same_row=bool(match.group(3)),
            )
            if button.same_row:
                current_row.append(button)
            else:
                if current_row:
                    buttons.append(current_row)
                current_row = [button]

    if current_row:
        buttons.append(current_row)

    return buttons


def parse_message_button(button: InlineKeyboardButton) -> Button | None:
    if button.url:
        return Button(
            text=button.text,
            action=ButtonAction.URL,
            data=button.url,
        )
    msg = "Actually, this button type is not supported. Only URL buttons are supported."
    raise UnknownMessageButtonTypeError(msg)


def parse_message_buttons_row(row: list[InlineKeyboardButton]) -> list[Button] | None:
    try:
        return [
            parsed_button
            for button in row
            if (parsed_button := parse_message_button(button)) is not None
        ]
    except UnknownMessageButtonTypeError:
        return None


def parse_message_buttons(reply_markup: InlineKeyboardMarkup) -> list[list[Button]]:
    return [
        parsed_row
        for row in reply_markup.inline_keyboard
        if (parsed_row := parse_message_buttons_row(row)) is not None
    ]
