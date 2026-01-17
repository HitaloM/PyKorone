from typing import Optional

from babel.support import LazyProxy

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import SophieButtonABC
from sophie_bot.utils.i18n import lazy_gettext as l_


class SophieDMButton(SophieButtonABC):
    button_type_names = ("sophieurl",)

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Sophie DM Button"), l_("Sophie DM Buttons")

    def examples(self) -> Optional[dict[str, Optional[LazyProxy]]]:
        return {
            "[Button name](btnsophieurl)": None,
        }
