from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, Type

from sophie_bot.db.models.button_action import ButtonAction
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.CaptchaButton import CaptchaButton
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.ConnectButton import ConnectButton
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.DeleteButton import DeleteButton
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.NoteButton import NoteButton
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.RulesButton import RulesButton
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieDMButton import SophieDMButton
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.URLButton import URLButton

if TYPE_CHECKING:
    from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import SophieButtonABC


class ButtonDefinition(NamedTuple):
    action: ButtonAction
    button_class: Type[SophieButtonABC]


BUTTON_DEFINITIONS = [
    ButtonDefinition(ButtonAction.url, URLButton),
    ButtonDefinition(ButtonAction.note, NoteButton),
    ButtonDefinition(ButtonAction.rules, RulesButton),
    ButtonDefinition(ButtonAction.delmsg, DeleteButton),
    ButtonDefinition(ButtonAction.connect, ConnectButton),
    ButtonDefinition(ButtonAction.captcha, CaptchaButton),
    ButtonDefinition(ButtonAction.sophiedm, SophieDMButton),
]

ALL_BUTTONS: list[SophieButtonABC] = [d.button_class() for d in BUTTON_DEFINITIONS]

ASS_MAPPING: dict[str, ButtonAction] = {
    ass_type: d.action for d in BUTTON_DEFINITIONS for ass_type in d.button_class.button_type_names
}
