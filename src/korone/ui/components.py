from typing import TYPE_CHECKING

from aiogram.utils.formatting import TextLink

from .expressions import Bullets, Column, Field, Numbered, Row, Section, Template

if TYPE_CHECKING:
    from aiogram.types import User

    from korone.utils.i18n import LazyProxy

    from .expression import Renderable, UIExpression


def column(*children: Renderable | None, gap: int = 0) -> UIExpression:
    return Column(children=children, gap=gap)


def row(*children: Renderable | None, separator: str = " · ") -> UIExpression:
    return Row(children=children, separator=separator)


def field(label: Renderable, value: Renderable, *, separator: str = ": ", bold: bool = True) -> UIExpression:
    return Field(label=label, value=value, separator=separator, bold=bold)


def section(title: Renderable, *children: Renderable | None, indent: str = "  ") -> UIExpression:
    return Section(title=title, children=children, indent=indent)


def bullets(*children: Renderable | None) -> UIExpression:
    return Bullets(children=children)


def numbered(*children: Renderable | None) -> UIExpression:
    return Numbered(children=children)


def template(source: str | LazyProxy, **values: Renderable) -> UIExpression:
    return Template(source=source, values=values)


def link(label: Renderable, target: str) -> TextLink:
    return TextLink(label, url=target)


def mention(user: User | int, name: str | None = None) -> TextLink:
    if isinstance(user, int):
        if name is None:
            msg = "A display name is required when mentioning a user by ID"
            raise ValueError(msg)
        user_id = user
        display_name = name
    else:
        user_id = user.id
        display_name = name or user.full_name

    return TextLink(display_name, url=f"tg://user?id={user_id}")
