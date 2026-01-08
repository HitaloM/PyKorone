import re
from abc import ABC
from functools import cached_property

from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgCustomError
from ass_tg.types.base_abc import ArgFabric

from sophie_bot.utils.i18n import gettext as _


class MarkdownLinkArgument(ArgFabric[tuple[str, str]], ABC):
    """
    Abstract Markdown link Argument.
    Example: [text](data)
    Does not check data at all.
    """

    know_the_end = True
    know_the_start = True

    _pattern = re.compile(r"\[(.*?)]\((.*?)\)")
    _pattern_chars = ("[", "]", "(", ")")

    # Used for classes that are based on this one
    _link_name: str
    _link_data: str

    ignored_entities: tuple[str, ...] = ("url", "text_link")
    separator = "]("

    @cached_property
    def data_offset(self) -> int:
        return len(self._link_name) + len(self.separator) + len("[](")

    def check(self, text: str, entities: ArgEntities) -> bool:
        text_match = self._pattern.match(text)
        if not text_match:
            return False

        self._link_name, self._link_data = text_match.groups()

        return True

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, tuple[str, str]]:
        text_match = self._pattern.match(text)
        if not text_match:
            raise ArgCustomError(_("Invalid markdown link."), offset=offset)
        link_name, link_data = text_match.groups()
        self._link_name, self._link_data = link_name, link_data

        length = len("[")

        # Check if link name has entities
        if entities.get_overlapping(1, len(link_name)):
            raise ArgCustomError(
                _("Markdown link name cannot contain entities."),
                offset=length + offset,
                length=len(link_name),
            )

        length += len(link_name)
        length += len("](")

        # Check if link_data has entities
        if entities := entities.get_overlapping(length, len(link_data) + 1):
            raise ArgCustomError(
                _("Markdown link data cannot contain entities."),
                offset=length + offset,
                length=len(link_data),  # include [](
            )

        length = len(link_name) + len(link_data) + len(self._pattern_chars)
        return length, (link_name, link_data)

    def get_end(self, raw_text: str, entities: ArgEntities) -> int:
        return raw_text.index(self._pattern_chars[-1])
