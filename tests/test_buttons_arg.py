import pytest
from ass_tg.entities import ArgEntities

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import AssButtonData
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.parse_arg import ButtonArg, ButtonsArg


@pytest.mark.asyncio
async def test_buttons_arg_many():
    arg = ButtonsArg()
    text = "[Google](btnurl:https://google.com) [Rules](btnrules)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0].button_type == "url"
    assert data[1].button_type == "rules"


@pytest.mark.asyncio
async def test_buttons_arg_many_newlines():
    arg = ButtonsArg()
    text = "[Google](btnurl:https://google.com)\n[Rules](btnrules)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0].button_type == "url"
    assert data[1].button_type == "rules"


@pytest.mark.asyncio
async def test_buttons_arg_url():
    arg = ButtonArg()
    text = "[Google](btnurl:https://google.com)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    assert parsed_arg.length == len(text)
    data = parsed_arg.value
    assert isinstance(data, AssButtonData)
    assert data.button_type == "url"
    assert data.arguments == ("https://google.com",)
    assert data.same_row is False


@pytest.mark.asyncio
async def test_buttons_arg_url_same_row():
    arg = ButtonArg()
    text = "[Google](btnurl:https://google.com:same)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "url"
    assert data.arguments == ("https://google.com",)
    assert data.same_row is True


@pytest.mark.asyncio
async def test_buttons_arg_note():
    arg = ButtonArg()
    text = "[Note](btnnote:my_note)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "note"
    assert data.arguments == ("my_note",)


@pytest.mark.asyncio
async def test_buttons_arg_rules():
    arg = ButtonArg()
    text = "[Rules](btnrules)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "rules"
    assert data.arguments == ("",)
    assert data.same_row is False


@pytest.mark.asyncio
async def test_buttons_arg_rules_same():
    arg = ButtonArg()
    text = "[Rules](btnrules:^)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "rules"
    assert data.arguments == ("",)
    assert data.same_row is True


@pytest.mark.asyncio
async def test_buttons_arg_delmsg():
    arg = ButtonArg()
    text = "[Delete](delmsg)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "delmsg"
    assert data.arguments == ("",)


@pytest.mark.asyncio
async def test_buttons_arg_delmsg_prefix():
    arg = ButtonArg()
    text = "[Delete](btndelmsg)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "delmsg"


@pytest.mark.asyncio
async def test_buttons_arg_connect():
    arg = ButtonArg()
    text = "[Connect](btnconnect)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "connect"


@pytest.mark.asyncio
async def test_buttons_arg_captcha():
    arg = ButtonArg()
    text = "[Captcha](btnwelcomesecurity)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "welcomesecurity"


@pytest.mark.asyncio
async def test_buttons_arg_sophie_dm():
    arg = ButtonArg()
    text = "[Sophie](btnsophieurl)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "sophieurl"


@pytest.mark.asyncio
async def test_buttons_arg_delmsg_prefix_button():
    arg = ButtonArg()
    text = "[Delete](buttondelmsg)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "delmsg"


@pytest.mark.asyncio
async def test_buttons_arg_note_same_row():
    arg = ButtonArg()
    text = "[Note](btnnote:my_note:same)"
    entities = ArgEntities([])

    assert arg.check(text, entities) is True

    parsed_arg = await arg(text, 0, entities)
    data = parsed_arg.value
    assert data.button_type == "note"
    assert data.arguments == ("my_note",)
    assert data.same_row is True


@pytest.mark.asyncio
async def test_buttons_arg_invalid_prefix():
    arg = ButtonArg()
    text = "[Google](invalidurl:https://google.com)"
    entities = ArgEntities([])

    from ass_tg.exceptions import ArgTypeError
    with pytest.raises(ArgTypeError):
        await arg(text, 0, entities)


@pytest.mark.asyncio
async def test_buttons_arg_invalid_button_type():
    arg = ButtonArg()
    text = "[Google](btninvalid:something)"
    entities = ArgEntities([])

    from ass_tg.exceptions import ArgTypeError
    with pytest.raises(ArgTypeError):
        await arg(text, 0, entities)


@pytest.mark.asyncio
async def test_buttons_arg_invalid():
    arg = ButtonArg()
    text = "Not a button"
    entities = ArgEntities([])

    from ass_tg.exceptions import ArgTypeError
    with pytest.raises(ArgTypeError):
        await arg(text, 0, entities)
