from __future__ import annotations

from aiogram.types import Message
from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgError
from stfu_tg import Section

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.TextWithButtonsArg import TextWithButtonsArg
from sophie_bot.modules.notes.utils.buttons_processor.buttons import ButtonsList
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _


async def parse_buttons_list_from_message(message: Message, text: str, offset: int = 0) -> tuple[str, ButtonsList]:
    try:
        arg = TextWithButtonsArg()
        entities = ArgEntities((getattr(message, "entities", None) or [])).cut_before(offset)
        _length, result = await arg.parse(text, 0, entities)
        note_text = result["text"].value
        buttons = ButtonsList.from_ass(result["buttons"].value)

        return note_text, buttons
    except ArgError as err:
        raise SophieException(
            Section(
                _("The buttons are not valid."),
                _("Please check the buttons documentation for the list of the allowed buttons."),
                *err.doc,
                title=_("Buttons are not valid."),
            )
        )
