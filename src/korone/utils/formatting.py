import re
from typing import TYPE_CHECKING, Self

from aiogram.utils.formatting import Bold as AiogramBold
from aiogram.utils.formatting import Code as AiogramCode
from aiogram.utils.formatting import Italic as AiogramItalic
from aiogram.utils.formatting import Text, TextLink, Underline

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from aiogram.types import MessageEntity

type Renderable = Text | object

_PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _keep_initial_item(item: Renderable | None) -> bool:
    return item is not None and not (isinstance(item, str) and not item)


class Element(Text):
    def to_html(self) -> str:
        return self.as_html()

    def __str__(self) -> str:
        return self.as_html()

    def __add__(self, other: Renderable) -> Doc:
        return Doc(self, other)


class Doc(Element):
    def __init__(self, *items: Renderable | None) -> None:
        self.items = tuple(item for item in items if _keep_initial_item(item))
        super().__init__(*self._join(self.items))

    @staticmethod
    def _join(items: Iterable[Renderable]) -> list[Renderable]:
        nodes: list[Renderable] = []
        for item in items:
            if nodes:
                nodes.append("\n")
            nodes.append(item)
        return nodes

    def __iadd__(self, other: Renderable | None) -> Self:
        if other is not None:
            self.items += (other,)
            self._body += (("\n", other) if self._body else (other,))
        return self

    def __iter__(self) -> Iterator[Renderable]:
        yield from self.items

    def render(
        self,
        *,
        _offset: int = 0,
        _sort: bool = True,
        _collect_entities: bool = True,
    ) -> tuple[str, list[MessageEntity]]:
        return Text(*self._body).render(
            _offset=_offset,
            _sort=_sort,
            _collect_entities=_collect_entities,
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} items={len(self.items)}>"


class StyleElement(Element):
    def __init__(self, item: Renderable | None) -> None:
        self.item = item
        super().__init__(*((item,) if item is not None else ()))


class Bold(AiogramBold, StyleElement):
    pass


class Italic(AiogramItalic, StyleElement):
    pass


class Code(AiogramCode, StyleElement):
    pass


class Url(TextLink, Element):
    def __init__(self, item: Renderable, link: str) -> None:
        self.link = link
        super().__init__(item, url=link)


class UserLink(Url):
    def __init__(self, user_id: int, name: str) -> None:
        self.user_id = user_id
        super().__init__(name, f"tg://user?id={user_id}")


class Template(Element):
    def __init__(self, item: object, **placeholders: Renderable) -> None:
        self.item = item
        self.placeholders = placeholders
        source = str(item)
        nodes: list[Renderable] = []
        position = 0

        for match in _PLACEHOLDER_PATTERN.finditer(source):
            nodes.append(source[position : match.start()])
            key = match.group(1)
            nodes.append(placeholders[key] if key in placeholders else match.group(0))
            position = match.end()

        nodes.append(source[position:])
        super().__init__(*nodes)


class Title(Element):
    def __init__(
        self, item: Renderable, prefix: Renderable = "[", postfix: Renderable = "]", *, bold: bool = True
    ) -> None:
        self.item = item
        self.prefix = prefix
        self.postfix = postfix
        self.bold = bold
        title = Text(prefix, item, postfix)
        super().__init__(Bold(title) if bold else title)


class KeyValue(Element):
    def __init__(
        self, title: Renderable, value: Renderable, suffix: Renderable = ": ", *, title_bold: bool = True
    ) -> None:
        self.title = title
        self.value = value
        self.suffix = suffix
        self.title_bold = title_bold
        super().__init__(Bold(title) if title_bold else title, suffix, value)


class HList(Doc):
    def __init__(self, *items: Renderable | None, prefix: Renderable = "", divider: Renderable = " ") -> None:
        self.items = tuple(item for item in items if _keep_initial_item(item))
        self.prefix = prefix
        self.divider = divider
        nodes: list[Renderable] = []
        for item in self.items:
            if nodes:
                nodes.append(divider)
            if prefix:
                nodes.append(prefix)
            nodes.append(item)
        Element.__init__(self, *nodes)


class VList(Doc):
    def __init__(self, *items: Renderable | None, indent: int = 0, prefix: Renderable = "- ") -> None:
        self.items = tuple(item for item in items if _keep_initial_item(item))
        self.prefix = prefix
        self.indent = indent
        Element.__init__(self, *self._nodes())

    def _nodes(self, additional_indent: int = 0) -> list[Renderable]:
        indent = self.indent + additional_indent
        space = " " * indent if indent else " "
        nodes: list[Renderable] = []
        for item in self.items:
            if nodes:
                nodes.append("\n")
            nodes.extend((space, self.prefix, item))
        return nodes

    def with_additional_indent(self, additional_indent: int) -> Text:
        return Text(*self._nodes(additional_indent))


class Section(Doc):
    def __init__(
        self,
        *items: Renderable | None,
        title: Renderable = "",
        title_underline: bool = True,
        title_bold: bool = False,
        indent: int = 1,
        indent_text: str = "  ",
        title_postfix: Renderable = ":",
    ) -> None:
        self.items = tuple(item for item in items if _keep_initial_item(item))
        self.title = title
        self.title_underline = title_underline
        self.title_bold = title_bold
        self.indent = indent
        self.indent_text = indent_text
        self.title_postfix = title_postfix
        Element.__init__(self, *self._nodes())

    def _nodes(self, additional_indent: int = 0) -> list[Renderable]:
        nodes: list[Renderable] = []
        if self.title:
            title: Renderable = self.title
            if self.title_underline:
                title = _Underline(title)
            if self.title_bold:
                title = Bold(title)
            nodes.extend((title, self.title_postfix))

        item_indent = self.indent + additional_indent
        for item in self.items:
            nodes.append("\n")
            if isinstance(item, Section):
                nodes.extend((self.indent_text * item_indent, item.with_additional_indent(item_indent)))
            elif isinstance(item, VList):
                nodes.append(item.with_additional_indent(item_indent * 2))
            else:
                nodes.extend((self.indent_text * item_indent, item))
        return nodes

    def with_additional_indent(self, additional_indent: int) -> Text:
        return Text(*self._nodes(additional_indent))

    def __iadd__(self, other: Renderable | None) -> Self:
        if other is not None:
            self.items += (other,)
            self._body = tuple(self._nodes())
        return self


class _Underline(Underline, StyleElement):
    pass
