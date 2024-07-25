from ass_tg.types.base_abc import ArgFabric
from sophie_bot.modules.help.cmds import CmdHelp
from stfu_tg import HList, VList, Template


def format_cmd(cmd: str):
    return f"/{cmd}"


def format_cmd_args(args: dict[str, ArgFabric]):
    return HList(*(f"<{arg.description}>" for arg in args.values()))


def format_cmds(all_cmds: list[CmdHelp]):
    return VList(*(
        Template(
            '{cmd} {args}',
            cmd=HList(*(format_cmd(cmd) for cmd in cmds.cmds)),
            args=format_cmd_args(cmds.args) if cmds.args else ""
        )
        for cmds in all_cmds
    ))