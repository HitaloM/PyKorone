# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from korone.modules.filters.utils.types import Button, ButtonAction


def unparse_buttons_to_text(buttons: list[list[Button]]) -> str:
    text_rows = []
    for row in buttons:
        text_buttons = [
            f"[{button.text}](buttonurl:{button.data}{":same" if button.same_row else ""})"
            for button in row
        ]
        text_rows.append(" ".join(text_buttons))
    return "\n".join(text_rows)


def unparse_button(button: Button) -> InlineKeyboardButton:
    if button.action == ButtonAction.URL:
        return InlineKeyboardButton(text=button.text, url=button.data)

    msg = f"Unsupported button action: {button.action}"
    raise NotImplementedError(msg)


def unparse_buttons(buttons: list[list[Button]]) -> InlineKeyboardMarkup:
    inline_keyboard = [[unparse_button(button) for button in row] for row in buttons]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
