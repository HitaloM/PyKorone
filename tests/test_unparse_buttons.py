from aiogram.types import InlineKeyboardButton

from sophie_bot.db.models.button_action import ButtonAction
from sophie_bot.modules.notes.utils.buttons_processor.buttons import Button
from sophie_bot.modules.notes.utils.buttons_processor.unparse import unparse_button, unparse_buttons


def test_unparse_button_url():
    button = Button(text="Google", action=ButtonAction.url, data="https://google.com")
    unparsed = unparse_button(button, 123)
    assert isinstance(unparsed, InlineKeyboardButton)
    assert unparsed.text == "Google"
    assert unparsed.url == "https://google.com"


def test_unparse_button_delmsg():
    button = Button(text="Delete", action=ButtonAction.delmsg, data=None)
    unparsed = unparse_button(button, 123)
    assert isinstance(unparsed, InlineKeyboardButton)
    assert unparsed.text == "Delete"
    assert unparsed.callback_data == "btn_deletemsg_cb_123"


def test_unparse_buttons():
    buttons = [
        [Button(text="R1C1", action=ButtonAction.url, data="https://r1c1.com")],
        [
            Button(text="R2C1", action=ButtonAction.url, data="https://r2c1.com"),
            Button(text="R2C2", action=ButtonAction.url, data="https://r2c2.com")
        ]
    ]
    markup = unparse_buttons(buttons, 123)
    assert len(markup.inline_keyboard) == 2
    assert len(markup.inline_keyboard[0]) == 1
    assert len(markup.inline_keyboard[1]) == 2
    assert markup.inline_keyboard[0][0].text == "R1C1"
    assert markup.inline_keyboard[1][1].url == "https://r2c2.com"
