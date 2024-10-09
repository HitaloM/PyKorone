from asyncio import iscoroutinefunction, run
from dataclasses import dataclass
from mailbox import Message
from types import ModuleType
from typing import Any, Callable, Coroutine, Dict, Optional

from aiogram import Router
from aiogram.filters.logic import _InvertFilter
from ass_tg.types.base_abc import ArgFabric
from babel.support import LazyProxy
from stfu_tg import Doc

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.chat_status import (
    ChatTypeFilter,
    LegacyOnlyGroups,
    LegacyOnlyPM,
)
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.user_status import IsAdmin, IsOP
from sophie_bot.utils.logger import log

ARGS_DICT = dict[str, ArgFabric]
ARGS_COROUTINE = Callable[
    [Optional[Message], Dict[str, Any]], Coroutine[Any, Any, ARGS_DICT]  # Args it takes  # What function returns
]


@dataclass
class CmdHelp:
    cmds: tuple[str, ...]
    args: Optional[ARGS_DICT]
    description: Optional[LazyProxy | str]
    only_admin: bool
    only_op: bool
    only_pm: bool
    only_chats: bool
    alias_to_modules: list[str]
    disableable: Optional[str]


@dataclass
class ModuleHelp:
    cmds: list[CmdHelp]
    name: LazyProxy | str
    icon: str
    exclude_public: bool
    info: str | LazyProxy | Doc
    description: str | LazyProxy | Doc


HELP_MODULES: dict[str, ModuleHelp] = {}
DISABLEABLE_CMDS: list[CmdHelp] = []


def get_aliased_cmds(module_name) -> dict[str, list[CmdHelp]]:
    return {
        mod_name: [cmd for cmd in module.cmds if cmd.alias_to_modules and module_name in cmd.alias_to_modules]
        for mod_name, module in HELP_MODULES.items()
        if any(cmd.alias_to_modules for cmd in module.cmds)
        and any(cmd.alias_to_modules and module_name in cmd.alias_to_modules for cmd in module.cmds)
    }


def gather_cmd_args(args: ARGS_DICT | ARGS_COROUTINE | None) -> ARGS_DICT | None:
    if not args:
        return None
    elif isinstance(args, dict):
        return args
    elif iscoroutinefunction(args):
        return run(args(None, {}))
    else:
        raise ValueError


def gather_cmds_help(router: Router) -> list[CmdHelp]:
    helps: list[CmdHelp] = []

    if router.sub_routers:
        helps.extend(*(gather_cmds_help(sub_router) for sub_router in router.sub_routers))

    for handler in router.message.handlers:
        if not handler.filters:
            continue

        cmd_filters = list(filter(lambda x: isinstance(x.callback, CMDFilter), handler.filters))

        if not cmd_filters:
            continue
        cmds = cmd_filters[0].callback.cmd  # type: ignore

        # Is admin
        only_admin = any(
            (isinstance(f.callback, IsAdmin) or (isinstance(f.callback, UserRestricting))) for f in handler.filters
        )

        # Only PMs
        only_pm = any(
            (
                (isinstance(f.callback, ChatTypeFilter) and f.callback.chat_type == "private")
                or (isinstance(f.callback, LegacyOnlyPM))
            )
            for f in handler.filters
        )

        # Only chats
        only_chats = any(
            (
                (isinstance(f.callback, ChatTypeFilter) and f.callback.chat_type != "private")
                or (
                    isinstance(f.callback, _InvertFilter)
                    and isinstance(f.callback.target.callback, ChatTypeFilter)
                    and f.callback.target.callback.chat_type == "private"
                )
                or (isinstance(f.callback, LegacyOnlyGroups))
            )
            for f in handler.filters
        )

        log.debug(f"Adding {cmds} to help")

        only_op = any(isinstance(f.callback, IsOP) for f in handler.filters)

        help_flags = handler.flags.get("help")

        if help_flags and help_flags.get("exclude"):
            continue

        if help_flags and help_flags.get("args"):
            args = gather_cmd_args(help_flags["args"])
        else:
            args = gather_cmd_args(handler.flags.get("args"))

        disableable = None
        if disableable_flag := handler.flags.get("disableable"):
            disableable = disableable_flag.name

        cmd = CmdHelp(
            cmds=cmds,
            args=args,
            description=help_flags.get("description", None) if help_flags else None,
            only_admin=only_admin,
            only_op=only_op,
            only_pm=only_pm,
            only_chats=only_chats,
            alias_to_modules=help_flags.get("alias_to_modules", None) if help_flags else [],
            disableable=disableable,
        )
        helps.append(cmd)

        if disableable:
            DISABLEABLE_CMDS.append(cmd)

    return helps


def gather_module_help(module: ModuleType) -> Optional[ModuleHelp]:
    if not hasattr(module, "router"):
        return None

    name: LazyProxy | str = getattr(module, "__module_name__", module.__name__.split(".")[-1])
    emoji = getattr(module, "__module_emoji__", "?")
    exclude_public = getattr(module, "__exclude_public__", False)
    info = getattr(module, "__module_info__", None)
    description = getattr(module, "__module_description__", None)

    if cmds := gather_cmds_help(module.router):
        return ModuleHelp(
            cmds=cmds, name=name, icon=emoji, exclude_public=exclude_public, info=info, description=description
        )
    else:
        return None
