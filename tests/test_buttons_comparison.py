import pytest
from aiogram.types import InlineKeyboardMarkup
from ass_tg.i18n import gettext_ctx

import sophie_bot.utils.i18n
from sophie_bot.config import CONFIG
from sophie_bot.modules.notes.utils.buttons_processor.buttons import ButtonsList
from sophie_bot.modules.notes.utils.buttons_processor.legacy import legacy_button_parser, BUTTONS

TEST_CASES = [
    # URL Button
    "[Google](buttonurl:https://google.com)",

    # Sophie URL
    "[Sophie](buttonsophieurl)",

    # Rules Button (Start button)
    "[Rules](buttonrules)",

    # DelMsg Button (Callback button)
    "[Delete](buttondelmsg)",

    # Connect Button (Start button)
    "[Connect](buttonconnect)",

    # Welcome Security (Start button)
    "[WS](buttonwelcomesecurity)",

    # Note button
    "[Note](buttonnote)",
    "[NoteArg](buttonnote:arg)",
    "[NoteHash](#NoteArg)",  # TODO: Enable when '#' syntax is supported by new parser

    # Same row test
    "[Btn1](buttonurl:https://1.com) [Btn2](buttonurl:https://2.com:same)",
]


class MockI18n:
    def get_current(self, no_error=False):
        return self

    def gettext(self, *args, **kwargs):
        return args[0] if args else ""

    def lazy_gettext(self, *args, **kwargs):
        return args[0] if args else ""


@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch):
    monkeypatch.setattr(CONFIG, "username", "SophieBot")

    mock = MockI18n()
    monkeypatch.setattr(sophie_bot.utils.i18n, "get_i18n", lambda: mock)
    gettext_ctx.set(mock)

    # Populate BUTTONS as they would be in the app
    BUTTONS.update({
        "rules": "btn_rules",
        "delmsg": "btn_deletemsg_cb",
        "welcomesecurity": "btnwelcomesecuritystart",
        "connect": "btn_connect_start",
        "note": "btnnotesm",
        "#": "btnnotesm",
    })


def compare_markups(markup1: InlineKeyboardMarkup, markup2: InlineKeyboardMarkup):
    """Compares two InlineKeyboardMarkup objects."""
    if not markup1.inline_keyboard and not markup2.inline_keyboard:
        return True

    rows1 = markup1.inline_keyboard
    rows2 = markup2.inline_keyboard

    if len(rows1) != len(rows2):
        print(f"Row count mismatch: {len(rows1)} vs {len(rows2)}")
        return False

    for i, (row1, row2) in enumerate(zip(rows1, rows2)):
        if len(row1) != len(row2):
            print(f"Row {i} length mismatch: {len(row1)} vs {len(row2)}")
            return False

        for j, (btn1, btn2) in enumerate(zip(row1, row2)):
            if btn1.text != btn2.text:
                print(f"Button {i},{j} text mismatch: '{btn1.text}' vs '{btn2.text}'")
                return False

            # Compare other attributes
            if btn1.url != btn2.url:
                print(f"Button {i},{j} url mismatch: '{btn1.url}' vs '{btn2.url}'")
                return False

            if btn1.callback_data != btn2.callback_data:
                print(f"Button {i},{j} callback_data mismatch: '{btn1.callback_data}' vs '{btn2.callback_data}'")
                return False

    return True


@pytest.mark.asyncio
@pytest.mark.parametrize("text", TEST_CASES)
async def test_compare_parsers(text):
    chat_id = 123456789

    # Legacy
    _, legacy_markup = legacy_button_parser(chat_id, text)

    # New
    new_markup = (await ButtonsList.from_text(text)).unparse(chat_id)

    assert compare_markups(legacy_markup, new_markup), f"Markup mismatch for input: {text}"
