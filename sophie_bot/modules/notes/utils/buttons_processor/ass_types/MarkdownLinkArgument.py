import re
from abc import ABC

from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgCustomError
from ass_tg.types.base_abc import ArgFabric, ArgValueType

from sophie_bot.utils.i18n import gettext as _


class MarkdownLinkArgument(ArgFabric, ABC):
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

    def check(self, text: str, entities: ArgEntities) -> bool:
        text_match = self._pattern.search(text)
        if not text_match:
            return False

        self._link_name, self._link_data = text_match.groups()

        # Check if any pattern chars have entities at their positions
        match_start = text_match.start()
        return not any(
            entities.index(match_start + text.index(char, match_start))
            for char in self._pattern_chars
            if char in text_match.group()
        )

    def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, ArgValueType]:
        text_match = self._pattern.search(text)
        if not text_match:
            raise ArgCustomError(_("Invalid markdown link."), offset=offset)
        link_name, link_data = text_match.groups()

        # Check if link name has entities
        if entities.index(offset + text.index(link_name, offset)) != offset:
            raise ArgCustomError(
                _("Markdown link name cannot contain entities."),
                offset=offset,
                length=len(link_name) + 1,  # include [
            )

        # Check if link_data has entities
        if entities.index(offset + text.index(link_data, offset)) != offset:
            raise ArgCustomError(
                _("Markdown link data cannot contain entities."),
                offset=offset,
                length=len(link_data) + 3,  # include [](
            )

        length = len(link_name) + len(link_data) + len(self._pattern_chars)
        return length, (link_name, link_data)
