import pytest
from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgCustomError

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import AssButtonData
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.URLButton import URLButton


@pytest.mark.asyncio
async def test_url_button_valid():
    button = URLButton()
    text = "[Google](btnurl:https://google.com)"
    entities = ArgEntities([])

    assert button.check(text, entities) is True

    length, data = await button.parse(text, 0, entities)
    assert length == len(text)
    assert isinstance(data, AssButtonData)
    assert data.button_type == "url"
    assert data.arguments == ("https://google.com",)
    assert data.same_row is False


@pytest.mark.asyncio
async def test_url_button_http():
    button = URLButton()
    text = "[Test](btnurl:http://example.com)"
    entities = ArgEntities([])

    assert button.check(text, entities) is True

    length, data = await button.parse(text, 0, entities)
    assert data.arguments == ("http://example.com",)


@pytest.mark.asyncio
async def test_url_button_same_row_same():
    button = URLButton()
    text = "[Google](btnurl:https://google.com:same)"
    entities = ArgEntities([])

    length, data = await button.parse(text, 0, entities)
    assert data.arguments == ("https://google.com",)
    assert data.same_row is True


@pytest.mark.asyncio
async def test_url_button_same_row_hat():
    button = URLButton()
    text = "[Google](btnurl:https://google.com:^)"
    entities = ArgEntities([])

    length, data = await button.parse(text, 0, entities)
    assert data.arguments == ("https://google.com",)
    assert data.same_row is True


@pytest.mark.asyncio
async def test_url_button_invalid_protocol():
    button = URLButton()
    text = "[Google](btnurl:ftp://google.com)"
    entities = ArgEntities([])

    assert button.check(text, entities) is True
    with pytest.raises(ArgCustomError) as excinfo:
        await button.parse(text, 0, entities)
    assert "URL must start with http or https" in str(excinfo.value)


@pytest.mark.asyncio
async def test_url_button_invalid_markdown():
    button = URLButton()
    text = "Not a button"
    entities = ArgEntities([])

    assert button.check(text, entities) is False


@pytest.mark.asyncio
async def test_url_button_wrong_prefix():
    button = URLButton()
    text = "[Google](other:https://google.com)"
    entities = ArgEntities([])

    assert button.check(text, entities) is False


@pytest.mark.asyncio
async def test_url_button_wrong_type():
    button = URLButton()
    text = "[Google](btnother:https://google.com)"
    entities = ArgEntities([])

    # SophieButtonABC.check might return True if prefix matches, but URLButton.check checks type
    assert button.check(text, entities) is False


@pytest.mark.asyncio
async def test_url_button_button_prefix():
    button = URLButton()
    text = "[Google](buttonurl:https://google.com)"
    entities = ArgEntities([])

    assert button.check(text, entities) is True
    length, data = await button.parse(text, 0, entities)
    assert data.button_type == "url"
    assert data.arguments == ("https://google.com",)
