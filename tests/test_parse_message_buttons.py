import pytest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from sophie_bot.db.models.button_action import ButtonAction
from sophie_bot.modules.notes.utils.buttons_processor.buttons import UnknownMessageButtonTypeError, \
    parse_message_button, parse_message_buttons_row, parse_message_buttons


def test_parse_message_button_url():
    button = InlineKeyboardButton(text="Google", url="https://google.com")
    parsed = parse_message_button(button)
    assert parsed.text == "Google"
    assert parsed.action == ButtonAction.url
    assert parsed.data == "https://google.com"


def test_parse_message_button_invalid():
    # Only url is supported for now in parse_message_button
    button = InlineKeyboardButton(text="Callback", callback_data="cb_data")
    with pytest.raises(UnknownMessageButtonTypeError):
        parse_message_button(button)


def test_parse_message_buttons_row():
    row = [
        InlineKeyboardButton(text="Google", url="https://google.com"),
        InlineKeyboardButton(text="Bing", url="https://bing.com"),
    ]
    parsed_row = parse_message_buttons_row(row)
    assert len(parsed_row) == 2
    assert parsed_row[0].text == "Google"
    assert parsed_row[1].text == "Bing"


def test_parse_message_buttons_row_with_invalid():
    row = [
        InlineKeyboardButton(text="Google", url="https://google.com"),
        InlineKeyboardButton(text="Invalid", callback_data="cb_data"),
    ]
    # parse_message_buttons_row catches UnknownMessageButtonTypeError and returns []
    parsed_row = parse_message_buttons_row(row)
    assert parsed_row == []


def test_parse_message_buttons():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Row1-Col1", url="https://r1c1.com")],
        [InlineKeyboardButton(text="Row2-Col1", url="https://r2c1.com"),
         InlineKeyboardButton(text="Row2-Col2", url="https://r2c2.com")]
    ])
    parsed_markup = parse_message_buttons(markup)
    assert len(parsed_markup) == 2
    assert len(parsed_markup[0]) == 1
    assert len(parsed_markup[1]) == 2
    assert parsed_markup[0][0].text == "Row1-Col1"
    assert parsed_markup[1][1].data == "https://r2c2.com"


def test_parse_message_buttons_empty():
    markup = InlineKeyboardMarkup(inline_keyboard=[])
    assert parse_message_buttons(markup) == []
