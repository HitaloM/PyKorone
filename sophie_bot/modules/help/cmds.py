from dataclasses import dataclass
from types import ModuleType
from typing import Optional

from aiogram import Router
from ass_tg.types.base_abc import ArgFabric
from babel.support import LazyProxy

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.logger import log


@dataclass
class CmdHelp:
    cmds: tuple[str, ...]
    args: Optional[dict[str, ArgFabric]]


@dataclass
class ModuleHelp:
    cmds: list[CmdHelp]
    name: LazyProxy | str
    icon: str


def gather_cmds_help(router: Router) -> list[CmdHelp]:
    helps = []
    for handler in router.message.handlers:
        if not handler.filters:
            continue

        cmd_filters = list(filter(lambda x: isinstance(x.callback, CMDFilter), handler.filters))

        if not cmd_filters:
            continue
        cmds = cmd_filters[0].callback.cmd  # type: ignore

        log.debug(f"Adding {cmds} to help")

        helps.append(CmdHelp(cmds=cmds, args=handler.flags.get("args")))
    return helps


def gather_module_help(module: ModuleType) -> Optional[ModuleHelp]:
    if not hasattr(module, "router"):
        return None

    name: LazyProxy | str = getattr(module, "__module_name__", "Unknown")
    emoji = getattr(module, "__module_emoji__", "?")

    return ModuleHelp(cmds=gather_cmds_help(module.router), name=name, icon=emoji)
