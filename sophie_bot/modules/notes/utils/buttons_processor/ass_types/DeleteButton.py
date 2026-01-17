from typing import Optional

from babel.support import LazyProxy

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import SophieButtonABC
from sophie_bot.utils.i18n import lazy_gettext as l_


class DeleteButton(SophieButtonABC):
    button_type_names = ("delmsg",)
    allowed_prefixes = ("btn", "button", "")

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Delete Button"), l_("Delete Buttons")

    def examples(self) -> Optional[dict[str, Optional[LazyProxy]]]:
        return {
            "[Button name](delmsg)": None,
        }
