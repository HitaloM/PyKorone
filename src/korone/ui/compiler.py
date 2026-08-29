from functools import singledispatch
from itertools import starmap
from string import Formatter

from aiogram.utils.formatting import Bold, Text, as_list, as_marked_list, as_numbered_list

from korone.utils.i18n import LazyProxy

from .expression import Renderable, UIExpression
from .expressions import Bullets, Column, Field, Numbered, Row, Section, Template

_FORMATTER = Formatter()


def _compile_text(text: Text) -> Text:
    return text.replace(*(compile_ui(node) for node in text))


def _children(nodes: tuple[Renderable | None, ...]) -> list[Text]:
    return [compile_ui(node) for node in nodes if node is not None]


def _as_list_or_empty(items: list[Text], *, separator: str = "\n") -> Text:
    if not items:
        return Text()
    return as_list(*items, sep=separator)


def _split_text_lines(text: Text) -> list[Text]:
    line_bodies: list[list[object]] = [[]]

    for node in text:
        fragments = tuple(_split_text_lines(node)) if isinstance(node, Text) else tuple(str(node).split("\n"))

        line_bodies[-1].append(fragments[0])
        line_bodies.extend([fragment] for fragment in fragments[1:])

    return list(starmap(text.replace, line_bodies))


def _indent_text(text: Text, prefix: str) -> Text:
    return _as_list_or_empty([Text(prefix, line) for line in _split_text_lines(text)])


def _bold_once(text: Text) -> Text:
    return text if isinstance(text, Bold) else Bold(text)


@singledispatch
def compile_ui(node: object) -> Text:
    if isinstance(node, UIExpression):
        msg = f"No UI compiler registered for {type(node).__name__}"
    else:
        msg = f"Unsupported UI value: {type(node).__name__}"
    raise TypeError(msg)


@compile_ui.register
def _compile_aiogram_text(node: Text) -> Text:
    return _compile_text(node)


@compile_ui.register
def _compile_scalar(node: str | int | float) -> Text:
    return Text(str(node))


@compile_ui.register
def _compile_lazy(node: LazyProxy) -> Text:
    return compile_ui(node.value)


@compile_ui.register
def _compile_column(node: Column) -> Text:
    return _as_list_or_empty(_children(node.children), separator="\n" * (node.gap + 1))


@compile_ui.register
def _compile_row(node: Row) -> Text:
    return _as_list_or_empty(_children(node.children), separator=node.separator)


@compile_ui.register
def _compile_field(node: Field) -> Text:
    label = compile_ui(node.label)
    return Text(_bold_once(label) if node.bold else label, node.separator, compile_ui(node.value))


@compile_ui.register
def _compile_section(node: Section) -> Text:
    title = _bold_once(compile_ui(node.title))
    children = _children(node.children)
    if not children:
        return Text(title)
    return _as_list_or_empty([title, *(_indent_text(child, node.indent) for child in children)])


@compile_ui.register
def _compile_bullets(node: Bullets) -> Text:
    children = _children(node.children)
    return as_marked_list(*children) if children else Text()


@compile_ui.register
def _compile_numbered(node: Numbered) -> Text:
    children = _children(node.children)
    return as_numbered_list(*children) if children else Text()


@compile_ui.register
def _compile_template(node: Template) -> Text:
    source = str(node.source)
    parts: list[object] = []

    for literal, field_name, format_spec, conversion in _FORMATTER.parse(source):
        if literal:
            parts.append(literal)
        if field_name is None:
            continue
        if not field_name.isidentifier():
            msg = "UI templates only support simple named placeholders"
            raise ValueError(msg)
        if format_spec or conversion:
            msg = "UI templates do not support conversions or format specifications"
            raise ValueError(msg)
        if field_name not in node.values:
            raise KeyError(field_name)
        parts.append(compile_ui(node.values[field_name]))

    return Text(*parts)
