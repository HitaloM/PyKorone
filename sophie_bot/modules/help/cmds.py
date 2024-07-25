from dataclasses import dataclass
from types import ModuleType
from typing import Optional

from aiogram import Router
from babel.support import LazyProxy

from ass_tg.types.base_abc import ArgFabric
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsAdmin, IsOP
from sophie_bot.utils.logger import log


@dataclass
class CmdHelp:
    cmds: tuple[str, ...]
    args: Optional[dict[str, ArgFabric]]
    only_admin: bool
    only_op: bool


@dataclass
class ModuleHelp:
    cmds: list[CmdHelp]
    name: LazyProxy | str
    icon: str
    exclude_public: bool


HELP_MODULES: dict[str, ModuleHelp] = {}


def gather_cmds_help(router: Router) -> list[CmdHelp]:
    helps = []
    for handler in router.message.handlers:
        if not handler.filters:
            continue

        cmd_filters = list(filter(lambda x: isinstance(x.callback, CMDFilter), handler.filters))

        if not cmd_filters:
            continue
        cmds = cmd_filters[0].callback.cmd  # type: ignore

        # Is admin
        only_admin = any(
            (isinstance(f.callback, IsAdmin) or (isinstance(f.callback, UserRestricting)))
            for f in handler.filters)
        log.debug(f"Adding {cmds} to help")

        only_op = any(
            isinstance(f.callback, IsOP) for f in handler.filters
        )

        helps.append(CmdHelp(
            cmds=cmds,
            args=handler.flags.get("args"),
            only_admin=only_admin,
            only_op=only_op
        ))
    return helps


def gather_module_help(module: ModuleType) -> Optional[ModuleHelp]:
    if not hasattr(module, "router"):
        return None

    name: LazyProxy | str = getattr(module, "__module_name__", module.__name__.split(".")[-1])
    emoji = getattr(module, "__module_emoji__", "?")
    exclude_public = getattr(module, "__exclude_public__", False)

    if cmds := gather_cmds_help(module.router):
        return ModuleHelp(cmds=cmds, name=name, icon=emoji, exclude_public=exclude_public)
    else:
        return None
