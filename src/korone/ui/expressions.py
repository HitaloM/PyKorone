from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .expression import Renderable, UIExpression

if TYPE_CHECKING:
    from collections.abc import Mapping

    from korone.utils.i18n import LazyProxy


@dataclass(frozen=True, slots=True)
class Column(UIExpression):
    children: tuple[Renderable | None, ...]
    gap: int = 0

    def __post_init__(self) -> None:
        if self.gap < 0:
            msg = "Column gap cannot be negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Row(UIExpression):
    children: tuple[Renderable | None, ...]
    separator: str = " · "


@dataclass(frozen=True, slots=True)
class Field(UIExpression):
    label: Renderable
    value: Renderable
    separator: str = ": "
    bold: bool = True


@dataclass(frozen=True, slots=True)
class Section(UIExpression):
    title: Renderable
    children: tuple[Renderable | None, ...]
    indent: str = "  "


@dataclass(frozen=True, slots=True)
class Bullets(UIExpression):
    children: tuple[Renderable | None, ...]


@dataclass(frozen=True, slots=True)
class Numbered(UIExpression):
    children: tuple[Renderable | None, ...]


@dataclass(frozen=True, slots=True)
class Template(UIExpression):
    source: str | LazyProxy
    values: Mapping[str, Renderable]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
