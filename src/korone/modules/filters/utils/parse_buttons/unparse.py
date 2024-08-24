# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from korone.modules.filters.utils.types import Button, ButtonAction


def unparse_button(button: Button) -> InlineKeyboardButton:
    if button.action == ButtonAction.URL:
        return InlineKeyboardButton(text=button.text, url=button.data)

    msg = f"Unsupported button action: {button.action}"
    raise NotImplementedError(msg)


def unparse_buttons(buttons: list[list[Button]]) -> InlineKeyboardMarkup:
    inline_keyboard = [[unparse_button(button) for button in row] for row in buttons]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
