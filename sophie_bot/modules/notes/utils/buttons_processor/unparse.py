from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sophie_bot.config import CONFIG
from sophie_bot.db.models.button_action import ButtonAction
from sophie_bot.db.models.notes_buttons import Button


def unparse_button(button: Button, chat_id: int) -> InlineKeyboardButton:
    action = button.action
    text = button.text
    data = button.data

    if action == ButtonAction.url:
        return InlineKeyboardButton(text=text, url=data)

    elif action == ButtonAction.sophiedm:
        return InlineKeyboardButton(text=text, url=f"https://t.me/{CONFIG.username}")

    elif action == ButtonAction.rules:
        cb = "btn_rules"
        string = f"{cb}_{chat_id}"
        return InlineKeyboardButton(text=text, url=f"https://t.me/{CONFIG.username}?start={string}")

    elif action == ButtonAction.delmsg:
        cb = "btn_deletemsg_cb"
        string = f"{cb}_{chat_id}"
        return InlineKeyboardButton(text=text, callback_data=string)

    elif action == ButtonAction.connect:
        cb = "btn_connect_start"
        string = f"{cb}_{chat_id}"
        return InlineKeyboardButton(text=text, url=f"https://t.me/{CONFIG.username}?start={string}")

    elif action == ButtonAction.captcha:
        cb = "btnwelcomesecuritystart"
        string = f"{cb}_{chat_id}"
        return InlineKeyboardButton(text=text, url=f"https://t.me/{CONFIG.username}?start={string}")

    elif action == ButtonAction.note:
        cb = "btnnotesm"
        string = f"{cb}_{data}_{chat_id}" if data else f"{cb}_{chat_id}"
        return InlineKeyboardButton(text=text, url=f"https://t.me/{CONFIG.username}?start={string}")

    # Fallback for unknown types (should not happen if all covered)
    return InlineKeyboardButton(text=text, callback_data="unknown")


def unparse_buttons(buttons: list[list[Button]], chat_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    for row in buttons:
        parsed_row = []
        for button in row:
            parsed_btn = unparse_button(button, chat_id)
            if parsed_btn:
                parsed_row.append(parsed_btn)
        if parsed_row:
            keyboard.append(parsed_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
