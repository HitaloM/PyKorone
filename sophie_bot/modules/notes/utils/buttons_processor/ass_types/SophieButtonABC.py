from abc import ABC

from ass_tg.entities import ArgEntities

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.MarkdownLinkArgument import MarkdownLinkArgument


class SophieButtonABC(MarkdownLinkArgument, ABC):
    button_type_names: tuple[str, ...]  # Must be defined in subclasses
    allowed_prefixes = (
        "button",
        "btn",
        "#",  # special case for notes
    )

    def check(self, text: str, entities: ArgEntities) -> bool:
        if not super().check(text, entities):
            return False

        # used_prefix = next((prefix for prefix in self.allowed_prefixes if self._link_data.startswith(prefix)), None)

        # data = self._link_data.removeprefix(used_prefix)

        return True
