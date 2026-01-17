from typing import Optional

from ass_tg.entities import ArgEntities
from babel.support import LazyProxy

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.MarkdownLinkArgument import MarkdownLinkArgument
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import SophieButtonABC, AssButtonData
from sophie_bot.utils.i18n import lazy_gettext as l_


class NoteButton(SophieButtonABC):
    button_type_names = ("note", "#")

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Note Button"), l_("Note Buttons")

    def examples(self) -> Optional[dict[str, Optional[LazyProxy]]]:
        return {
            "[Button name](btnnote:note_name)": None,
        }

    def check(self, text: str, entities: ArgEntities) -> bool:
        if not MarkdownLinkArgument.check(self, text, entities):
            return False

        if self._link_data.startswith("#"):
            return True

        return super().check(text, entities)

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, AssButtonData[str]]:
        if self._link_data.startswith("#"):
            length, (link_name, link_data) = await MarkdownLinkArgument.parse(self, text, offset, entities)

            raw_arg = link_data[1:]
            arg = raw_arg
            same_row = False

            for suffix in self.same_row_suffixes:
                if raw_arg.endswith(":" + suffix):
                    same_row = True
                    arg = raw_arg[: -len(suffix) - 1]
                    break

            return length, AssButtonData(button_type="#", title=link_name, arguments=(arg,), same_row=same_row)

        return await super().parse(text, offset, entities)
