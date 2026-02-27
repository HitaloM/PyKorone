from __future__ import annotations

from typing import TYPE_CHECKING

from stfu_tg import Code, HList, Italic, Section, Template, VList

from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from ass_tg.types.base_abc import ArgFabric
    from stfu_tg.doc import Element

    from korone.modules.help.utils.extract_info import HandlerHelp
    from korone.utils.i18n import LazyProxy


def format_cmd(cmd: str, *, raw: bool = False) -> Element:
    return Code(cmd if raw else f"/{cmd}")


def format_cmd_args(arguments: Mapping[str, ArgFabric], *, as_code: bool = False) -> HList:
    formatted: list[Element | str] = []
    for arg in arguments.values():
        if arg.description is None:
            continue

        rendered = f"<{arg.description}>"
        formatted.append(Code(rendered) if as_code else rendered)

    return HList(*formatted)


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
    if not handler.description or not show_description:
        return title

    return Section(
        Italic(handler.description), title=title, title_bold=False, title_underline=False, title_postfix="", indent=2
    )


def format_handlers(all_cmds: Sequence[HandlerHelp], **kwargs: bool) -> VList:
    return VList(*(format_handler(handler, **kwargs) for handler in all_cmds))


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
