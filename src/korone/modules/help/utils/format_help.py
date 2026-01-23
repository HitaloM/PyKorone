from typing import Sequence

from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Code, HList, Italic, Section, VList
from stfu_tg.doc import Element

from korone.modules.help.utils.extract_info import HandlerHelp
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


def format_cmd(cmd: str) -> Element:
    return Code(f"/{cmd}")


def format_cmd_args(arguments: dict[str, ArgFabric], as_code: bool = False) -> HList:
    formatted_descriptions = (
        Code(f"<{arg.description}>") if as_code else f"<{arg.description}>" for arg in arguments.values()
    )
    return HList(*formatted_descriptions)


def format_handler(handler: HandlerHelp, show_only_in_groups: bool = True, show_disable_able: bool = True):
    cmd_and_args = HList(
        HList(*(format_cmd(cmd) for cmd in handler.cmds)),
        format_cmd_args(handler.args) if handler.args else None,
        Italic(_("— Only in groups")) if show_only_in_groups and handler.only_chats else None,
        Italic("({})".format(_("Disable-able"))) if show_disable_able and handler.disableable else None,
    )
    if not handler.description:
        return cmd_and_args

    return Section(
        Italic(handler.description),
        title=cmd_and_args,
        title_bold=False,
        title_underline=False,
        title_postfix="",
        indent=2,
    )


def format_handlers(all_cmds: Sequence[HandlerHelp], **kwargs):
    return VList(*(format_handler(handler, **kwargs) for handler in all_cmds))


def group_handlers(handlers: Sequence[HandlerHelp]) -> list[tuple[LazyProxy, list[HandlerHelp]]]:
    cmds = []
    pm_cmds = []
    admin_only_cmds = []

    for handler in handlers:
        if handler.only_op:
            continue

        if handler.only_pm:
            pm_cmds.append(handler)
        elif handler.only_admin:
            admin_only_cmds.append(handler)
        else:
            cmds.append(handler)

    groups = []

    if cmds:
        groups.append((l_("Commands"), cmds))
    if pm_cmds:
        groups.append((l_("PM-only"), pm_cmds))
    if admin_only_cmds:
        groups.append((l_("Only admins"), admin_only_cmds))

    return groups
