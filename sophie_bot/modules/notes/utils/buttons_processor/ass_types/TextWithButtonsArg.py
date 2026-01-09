from libs.ass.ass_tg.types.logic import OptionalArg
from libs.ass.ass_tg.types.reverse import ReverseArg
from libs.ass.ass_tg.types.text import TextArg
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.parse_arg import ButtonsArg
from sophie_bot.utils.i18n import lazy_gettext as l_


class TextWithButtonsArg(ReverseArg):
    def __init__(self):
        super().__init__(
            text=OptionalArg(TextArg(l_("Content"), parse_entities=True)),
            # `ButtonsArg` already safely parses to `[]` when no buttons are present,
            # and it needs to be able to provide `get_start()` for `ReverseArg`.
            buttons=ButtonsArg(l_("Buttons")),
        )
