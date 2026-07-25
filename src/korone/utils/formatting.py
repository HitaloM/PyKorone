import html
import re
from abc import ABC, abstractmethod
from typing import ClassVar, Self

type Renderable = Element | object

_PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _escape_html(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_html(item: Renderable) -> str:
    if isinstance(item, Element):
        return item.to_html()
    return _escape_html(item)


def _keep_initial_item(item: Renderable | None) -> bool:
    return item is not None and not (isinstance(item, str) and not item)


class Element(ABC):
    @abstractmethod
    def to_html(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.to_html()

    def __add__(self, other: Renderable) -> Doc:
        return Doc(self, other)


class Doc(Element, list[Renderable]):
    def __init__(self, *items: Renderable | None) -> None:
        list.__init__(self, [item for item in items if _keep_initial_item(item)])

    def __iadd__(self, other: Renderable | None) -> Self:
        if other is not None:
            self.append(other)
        return self

    def to_html(self) -> str:
        return "\n".join(_render_html(item) for item in self)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} items={len(self)}>"


class StyleElement(Element):
    prefix: ClassVar[str]
    postfix: ClassVar[str]

    __slots__ = ("item",)

    def __init__(self, item: Renderable | None) -> None:
        self.item = item

    def to_html(self) -> str:
        if self.item is None:
            return ""
        rendered = _render_html(self.item)
        if not rendered:
            return ""
        return f"{self.prefix}{rendered}{self.postfix}"


class Bold(StyleElement):
    prefix = "<b>"
    postfix = "</b>"


class Italic(StyleElement):
    prefix = "<i>"
    postfix = "</i>"


class Code(StyleElement):
    prefix = "<code>"
    postfix = "</code>"


class Url(StyleElement):
    prefix = "<a>"
    postfix = "</a>"

    __slots__ = ("link",)

    def __init__(self, item: Renderable, link: str) -> None:
        super().__init__(item)
        self.link = link

    def to_html(self) -> str:
        rendered = _render_html(self.item)
        if not rendered:
            return ""
        link = html.escape(self.link, quote=True)
        return f'<a href="{link}">{rendered}</a>'


class UserLink(Url):
    __slots__ = ("user_id",)

    def __init__(self, user_id: int, name: str) -> None:
        self.user_id = user_id
        super().__init__(name, f"tg://user?id={user_id}")


class Template(Element):
    __slots__ = ("item", "placeholders")

    def __init__(self, item: object, **placeholders: Renderable) -> None:
        self.item = item
        self.placeholders = placeholders

    def to_html(self) -> str:
        source = str(self.item)
        parts: list[str] = []
        position = 0

        for match in _PLACEHOLDER_PATTERN.finditer(source):
            parts.append(_escape_html(source[position : match.start()]))
            key = match.group(1)
            value = self.placeholders.get(key)
            parts.append(_render_html(value) if key in self.placeholders else match.group(0))
            position = match.end()

        parts.append(_escape_html(source[position:]))
        return "".join(parts)


class Title(Element):
    __slots__ = ("bold", "item", "postfix", "prefix")

    def __init__(
        self, item: Renderable, prefix: Renderable = "[", postfix: Renderable = "]", *, bold: bool = True
    ) -> None:
        self.item = item
        self.prefix = prefix
        self.postfix = postfix
        self.bold = bold

    def to_html(self) -> str:
        rendered = f"{_render_html(self.prefix)}{_render_html(self.item)}{_render_html(self.postfix)}"
        return f"<b>{rendered}</b>" if self.bold else rendered


class KeyValue(Element):
    __slots__ = ("suffix", "title", "title_bold", "value")

    def __init__(
        self, title: Renderable, value: Renderable, suffix: Renderable = ": ", *, title_bold: bool = True
    ) -> None:
        self.title = title
        self.value = value
        self.suffix = suffix
        self.title_bold = title_bold

    def to_html(self) -> str:
        title = _render_html(self.title)
        if self.title_bold and title:
            title = f"<b>{title}</b>"
        return f"{title}{_render_html(self.suffix)}{_render_html(self.value)}"


class HList(Doc):
    def __init__(self, *items: Renderable | None, prefix: Renderable = "", divider: Renderable = " ") -> None:
        super().__init__(*items)
        self.prefix = prefix
        self.divider = divider

    def to_html(self) -> str:
        prefix = _render_html(self.prefix) if self.prefix else ""
        divider = _render_html(self.divider)
        return divider.join(f"{prefix}{_render_html(item)}" for item in self)


class VList(Doc):
    def __init__(self, *items: Renderable | None, indent: int = 0, prefix: Renderable = "- ") -> None:
        super().__init__(*items)
        self.prefix = prefix
        self.indent = indent

    def to_html(self, additional_indent: int = 0) -> str:
        indent = self.indent + additional_indent
        space = " " * indent if indent else " "
        if not isinstance(self.prefix, Element) and all(not isinstance(item, Element) for item in self):
            line_prefix = f"{space}{self.prefix}"
            return _escape_html("\n".join(f"{line_prefix}{item}" for item in self))

        prefix = _render_html(self.prefix)
        return "\n".join(f"{space}{prefix}{_render_html(item)}" for item in self)


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
        super().__init__(*items)
        self.title = title
        self.title_underline = title_underline
        self.title_bold = title_bold
        self.indent = indent
        self.indent_text = indent_text
        self.title_postfix = title_postfix

    def to_html(self, additional_indent: int = 0) -> str:
        parts: list[str] = []
        if self.title:
            title = _render_html(self.title)
            if self.title_underline:
                title = f"<u>{title}</u>"
            if self.title_bold:
                title = f"<b>{title}</b>"
            parts.extend((title, _render_html(self.title_postfix)))

        item_indent = self.indent + additional_indent
        for item in self:
            parts.append("\n")
            if isinstance(item, Section):
                parts.extend((self.indent_text * item_indent, item.to_html(additional_indent=item_indent)))
            elif isinstance(item, VList):
                parts.append(item.to_html(additional_indent=item_indent * 2))
            else:
                parts.extend((self.indent_text * item_indent, _render_html(item)))

        return "".join(parts)
