from typing import Sequence

from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Code, HList, Italic, Section, VList
from stfu_tg.doc import Element

from sophie_bot.modules.help.utils.extract_info import CmdHelp
from sophie_bot.utils.i18n import gettext as _


def format_cmd(cmd: str) -> Element:
    return Code(f"/{cmd}")


def format_cmd_args(args: dict[str, ArgFabric]):
    return HList(*(f"<{arg.description}>" for arg in args.values()))


def format_handler(handler: CmdHelp, show_only_in_groups: bool = True, show_disable_able: bool = True):
    cmd_and_args = HList(
        HList(*(format_cmd(cmd) for cmd in handler.cmds)),
        format_cmd_args(handler.args) if handler.args else None,
        Italic(_("— Only in groups")) if show_only_in_groups and handler.only_chats else None,
        Italic("({})".format(_("Disable-able"))) if show_disable_able and handler.disableable else None,
    )
    if not handler.description:
        return cmd_and_args

    # TODO: Fix indents in ASS
    return Section(
        Italic(handler.description),
        title=cmd_and_args,
        title_bold=False,
        title_underline=False,
        title_postfix="",
        indent=3,
    )


def format_cmds(all_cmds: Sequence[CmdHelp], **kwargs):
    return VList(*(format_handler(handler, **kwargs) for handler in all_cmds))
