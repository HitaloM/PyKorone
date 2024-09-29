from ass_tg.types.base_abc import ArgFabric
from stfu_tg import HList, Italic, Section, Template, VList

from sophie_bot.modules.help.utils.extract_info import CmdHelp
from sophie_bot.utils.i18n import gettext as _


def format_cmd(cmd: str):
    return f"/{cmd}"


def format_cmd_args(args: dict[str, ArgFabric]):
    return HList(*(f"<{arg.description}>" for arg in args.values()))


def format_handler(handler: CmdHelp):

    template = "{cmd} {args}"

    if handler.only_chats:
        template += _(" - Only in chats")

    cmd_and_args = Template(
        template,
        cmd=HList(*(format_cmd(cmd) for cmd in handler.cmds)),
        args=format_cmd_args(handler.args) if handler.args else "",
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


def format_cmds(all_cmds: list[CmdHelp]):
    return VList(*(format_handler(handler) for handler in all_cmds))
