import pytest
from ass_tg.entities import ArgEntities
from ass_tg.i18n import gettext_ctx
from ass_tg.types import TextArg, ReverseArg

import sophie_bot.utils.i18n
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.parse_arg import ButtonsArg
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.TextWithButtonsArg import TextWithButtonsArg


class MockI18n:
    def get_current(self, no_error=False):
        return self

    def gettext(self, *args, **kwargs):
        return args[0] if args else ""

    def lazy_gettext(self, *args, **kwargs):
        return args[0] if args else ""


@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch):
    mock = MockI18n()
    monkeypatch.setattr(sophie_bot.utils.i18n, "get_i18n", lambda: mock)
    gettext_ctx.set(mock)


@pytest.mark.asyncio
async def test_reverse_arg_text_and_buttons():
    # Use kwargs for ReverseArg
    arg = ReverseArg(text=TextArg(), buttons=ButtonsArg())
    # Note: URLButton requires 'btn' or 'button' prefix and valid protocol
    text = "This is a note.\n[Button](btnurl:https://google.com)"
    entities = ArgEntities([])

    assert arg.check(text, entities)

    length, result = await arg.parse(text, 0, entities)

    assert length == len(text)
    assert isinstance(result, dict)
    text_res = result['text'].value
    buttons_res = result['buttons'].value

    # ReverseArg strips whitespace between args
    assert text_res == "This is a note."
    assert isinstance(buttons_res, list)
    assert len(buttons_res) == 1
    assert buttons_res[0].title == "Button"
    assert buttons_res[0].button_type == "url"
    assert buttons_res[0].arguments[0] == "https://google.com"


@pytest.mark.asyncio
async def test_reverse_arg_multiple_buttons():
    arg = ReverseArg(text=TextArg(), buttons=ButtonsArg())
    # Note: URLButton requires 'btn' or 'button' prefix and valid protocol
    text = "Text\n[Btn1](btnurl:https://1.com) [Btn2](btnurl:https://2.com)"
    entities = ArgEntities([])

    assert arg.check(text, entities)
    length, result = await arg.parse(text, 0, entities)

    text_res = result['text'].value
    buttons_res = result['buttons'].value
    assert text_res == "Text"
    assert len(buttons_res) == 2
    assert buttons_res[0].title == "Btn1"
    assert buttons_res[1].title == "Btn2"


@pytest.mark.asyncio
async def test_reverse_arg_only_text():
    # Buttons are optional: when no button syntax is present, ButtonsArg should parse to an empty list.
    arg = ReverseArg(text=TextArg(), buttons=ButtonsArg())
    text = "Just text"
    entities = ArgEntities([])

    # ReverseArg.check returns True unconditionally in ass_tg
    assert arg.check(text, entities)

    length, result = await arg.parse(text, 0, entities)
    assert length == len(text)
    assert result["text"].value == text
    assert result["buttons"].value == []


@pytest.mark.asyncio
async def test_reverse_arg_buttons_with_newlines():
    # Buttons usually at the end, can have newlines before them?
    # ReverseArg splits string.
    arg = ReverseArg(text=TextArg(), buttons=ButtonsArg())
    text = "Text\n\n[Btn](btnurl:https://google.com)"
    entities = ArgEntities([])

    assert arg.check(text, entities)
    length, result = await arg.parse(text, 0, entities)

    text_res = result['text'].value
    # TextArg should capture everything before the button
    assert text_res == "Text"


@pytest.mark.asyncio
async def test_text_with_buttons_arg_text_and_buttons():
    arg = TextWithButtonsArg()
    text = "This is a note.\n[Button](btnurl:https://google.com)"
    entities = ArgEntities([])

    assert arg.check(text, entities)
    length, result = await arg.parse(text, 0, entities)

    assert length == len(text)
    assert result["text"].value == "This is a note."
    buttons_res = result["buttons"].value
    assert isinstance(buttons_res, list)
    assert len(buttons_res) == 1
    assert buttons_res[0].title == "Button"


@pytest.mark.asyncio
async def test_text_with_buttons_arg_only_text_buttons_empty_list():
    arg = TextWithButtonsArg()
    text = "Just text"
    entities = ArgEntities([])

    assert arg.check(text, entities)
    length, result = await arg.parse(text, 0, entities)

    assert length == len(text)
    assert result["text"].value == text
    # Important contract: callers expect `buttons` to be a list, even when absent.
    assert result["buttons"].value == []
