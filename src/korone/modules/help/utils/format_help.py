from string import Formatter
from typing import TYPE_CHECKING

from aiogram.types import (
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockParagraph,
    RichTextBotCommand,
    RichTextCode,
    RichTextItalic,
)

from korone.utils.formatting import Code, Doc, Element, HList, Italic, Section, Template, VList
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from aiogram.types import InputRichBlockUnion, RichTextUnion

    from korone.args import Argument
    from korone.modules.help.utils.extract_info import HandlerHelp
    from korone.utils.i18n import LazyProxy


def format_cmd(cmd: str, *, raw: bool = False) -> Element:
    return Code(cmd if raw else f"/{cmd}")


def format_cmd_args(arguments: Mapping[str, Argument[object]], *, as_code: bool = False) -> HList:
    formatted: list[Element | str] = []
    for arg in arguments.values():
        if arg.help_description is None:
            continue

        rendered = f"<{arg.help_description}>"
        formatted.append(Code(rendered) if as_code else rendered)

    return HList(*formatted)


def _format_example_text(handler: HandlerHelp, example: str) -> str:
    normalized_example = example.strip()
    if not normalized_example:
        return ""

    if normalized_example.startswith(("/", "!")):
        return normalized_example

    command = handler.cmds[0] if handler.cmds else ""
    command_prefix = command if handler.raw_cmds else f"/{command}"
    return f"{command_prefix} {normalized_example}".strip()


def _format_example(handler: HandlerHelp, example: str) -> Element:
    return Code(_format_example_text(handler, example))


def _format_example_entry(handler: HandlerHelp, label: object, example: str) -> Element:
    formatted_example = _format_example(handler, example)
    if label is None:
        return formatted_example

    return Section(formatted_example, title=label, title_bold=False, title_underline=False, title_postfix="", indent=1)


def format_handler(
    handler: HandlerHelp,
    *,
    show_only_in_groups: bool = True,
    show_disable_able: bool = True,
    show_description: bool = True,
    show_args: bool = True,
) -> Element:
    title = HList(
        HList(*(format_cmd(cmd, raw=handler.raw_cmds) for cmd in handler.cmds)),
        format_cmd_args(handler.args) if handler.args and show_args else None,
        Italic(_("— Only in groups")) if show_only_in_groups and handler.only_chats else None,
        Italic(Template("({label})", label=_("Toggleable"))) if show_disable_able and handler.disableable else None,
    )
    if handler.description and show_description:
        return Section(
            Italic(handler.description),
            title=title,
            title_bold=False,
            title_underline=False,
            title_postfix="",
            indent=2,
        )

    return title


def format_handlers(all_cmds: Sequence[HandlerHelp], **kwargs: bool) -> VList:
    return VList(*(format_handler(handler, **kwargs) for handler in all_cmds))


def format_example_items(all_cmds: Sequence[HandlerHelp]) -> list[Element]:
    return [
        _format_example_entry(handler, label, example) for handler in all_cmds for label, example in handler.examples
    ]


def format_rich_text(value: object) -> RichTextUnion:
    if not isinstance(value, Doc):
        return str(value)

    parts: list[RichTextUnion] = []
    for item in value:
        if parts:
            parts.append("\n")
        parts.append(str(item))
    return parts


def format_rich_template(template: object, **placeholders: RichTextUnion) -> RichTextUnion:
    parts: list[RichTextUnion] = []
    for literal, field_name, format_spec, conversion in Formatter().parse(str(template)):
        if literal:
            parts.append(literal)
        if field_name is None:
            continue
        if format_spec or conversion:
            msg = "Rich-text templates only support simple placeholders"
            raise ValueError(msg)
        try:
            parts.append(placeholders[field_name])
        except KeyError as exc:
            msg = f"Missing rich-text template placeholder: {field_name}"
            raise ValueError(msg) from exc
    return parts


def _format_rich_command(handler: HandlerHelp, command: str) -> RichTextUnion:
    if handler.raw_cmds:
        return RichTextCode(text=command)

    command_text = f"/{command}"
    return RichTextBotCommand(text=command_text, bot_command=command_text)


def format_rich_handler(handler: HandlerHelp) -> RichTextUnion:
    parts: list[RichTextUnion] = []
    for command in handler.cmds:
        if parts:
            parts.append(" ")
        parts.append(_format_rich_command(handler, command))

    if handler.args:
        for argument in handler.args.values():
            if argument.help_description is None:
                continue
            parts.extend((" ", RichTextCode(text=f"<{argument.help_description}>")))

    if handler.only_chats:
        parts.extend((" ", RichTextItalic(text=str(_("— Only in groups")))))
    if handler.disableable:
        parts.extend((" ", RichTextItalic(text=f"({_('Toggleable')})")))
    if handler.description:
        parts.extend((": ", str(handler.description)))
    return parts


def format_rich_handlers(all_cmds: Sequence[HandlerHelp]) -> InputRichBlockList:
    return InputRichBlockList(
        items=[
            InputRichBlockListItem(blocks=[InputRichBlockParagraph(text=format_rich_handler(handler))])
            for handler in all_cmds
        ]
    )


def format_rich_examples(all_cmds: Sequence[HandlerHelp]) -> list[InputRichBlockUnion]:
    examples: list[InputRichBlockUnion] = []
    for handler in all_cmds:
        for label, example in handler.examples:
            formatted_example = RichTextCode(text=_format_example_text(handler, example))
            if label is None:
                examples.append(InputRichBlockParagraph(text=formatted_example))
                continue

            examples.append(InputRichBlockParagraph(text=[str(label), "\n  ", formatted_example]))
    return examples


def format_examples(all_cmds: Sequence[HandlerHelp]) -> Section | None:
    examples = format_example_items(all_cmds)

    if not examples:
        return None

    return Section(*examples, title=_("Examples"))


def group_handlers(handlers: Sequence[HandlerHelp]) -> list[tuple[LazyProxy, list[HandlerHelp]]]:
    default_cmds: list[HandlerHelp] = []
    pm_only_cmds: list[HandlerHelp] = []
    admin_only_cmds: list[HandlerHelp] = []

    for handler in handlers:
        if handler.only_op:
            continue

        if handler.only_pm:
            pm_only_cmds.append(handler)
        elif handler.only_admin:
            admin_only_cmds.append(handler)
        else:
            default_cmds.append(handler)

    groups: list[tuple[LazyProxy, list[HandlerHelp]]] = []

    if default_cmds:
        groups.append((l_("Commands"), default_cmds))
    if pm_only_cmds:
        groups.append((l_("PM-only"), pm_only_cmds))
    if admin_only_cmds:
        groups.append((l_("Only admins"), admin_only_cmds))

    return groups
