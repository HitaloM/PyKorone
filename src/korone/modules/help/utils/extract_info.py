from collections import OrderedDict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from inspect import isawaitable, iscoroutinefunction
from itertools import chain
from typing import TYPE_CHECKING, cast

from aiogram.enums import ChatType
from aiogram.filters.logic import _InvertFilter
from aiogram.types import Message
from ass_tg.types.base_abc import ArgFabric

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import ChatTypeFilter
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.logger import get_logger
from korone.utils.handlers import HandlerData

if TYPE_CHECKING:
    from types import ModuleType

    from aiogram import Router
    from babel.support import LazyProxy
    from stfu_tg import Doc

ARGS_DICT = dict[str, ArgFabric]
ARGS_COROUTINE = Callable[[Message | None, HandlerData], Coroutine[None, None, ARGS_DICT]]

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class HandlerHelp:
    cmds: tuple[str, ...]
    args: ARGS_DICT | None
    description: LazyProxy | str | None
    only_admin: bool
    only_op: bool
    only_pm: bool
    only_chats: bool
    alias_to_modules: list[str]
    disableable: str | None
    raw_cmds: bool


@dataclass(slots=True)
class ModuleHelp:
    handlers: list[HandlerHelp]
    name: LazyProxy | str
    icon: str
    exclude_public: bool
    info: str | LazyProxy | Doc
    description: str | LazyProxy | Doc


HELP_MODULES: OrderedDict[str, ModuleHelp] = OrderedDict()
DISABLEABLE_CMDS: list[HandlerHelp] = []


def get_aliased_cmds(module_name: str) -> dict[str, list[HandlerHelp]]:
    aliased: dict[str, list[HandlerHelp]] = {}
    for mod_name, module in HELP_MODULES.items():
        handlers = [cmd for cmd in module.handlers if cmd.alias_to_modules and module_name in cmd.alias_to_modules]
        if handlers:
            aliased[mod_name] = handlers
    return aliased


def get_all_cmds() -> list[HandlerHelp]:
    return [cmd for module in HELP_MODULES.values() for cmd in module.handlers]


def get_all_cmds_raw() -> tuple[str, ...]:
    return tuple(chain.from_iterable(cmds.cmds for cmds in get_all_cmds()))


def normalize_cmds(cmds: object) -> tuple[str, ...] | None:
    if isinstance(cmds, str):
        return (cmds,)
    if isinstance(cmds, (list, tuple)) and all(isinstance(cmd, str) for cmd in cmds):
        return cast("tuple[str, ...]", tuple(cmds))
    return None


async def gather_cmd_args(args: ARGS_DICT | ARGS_COROUTINE | None) -> ARGS_DICT | None:
    if not args:
        return None
    if isinstance(args, dict):
        return cast("ARGS_DICT", args)
    if callable(args):
        result = args(None, {})
        if iscoroutinefunction(args) or isawaitable(result):
            result = await result
        return cast("ARGS_DICT", result)
    msg = "Unsupported args type"
    raise TypeError(msg)


async def gather_cmds_help(router: Router) -> list[HandlerHelp]:
    helps: list[HandlerHelp] = []

    for sub_router in router.sub_routers:
        helps.extend(await gather_cmds_help(sub_router))

    for handler in router.message.handlers:
        if not handler.filters:
            continue

        help_flags = handler.flags.get("help")
        if help_flags and help_flags.get("exclude"):
            continue

        cmd_filters = [f for f in handler.filters if isinstance(f.callback, CMDFilter)]
        cmds = None
        if cmd_filters:
            cmd_callback = cmd_filters[0].callback
            if hasattr(cmd_callback, "cmd"):
                cmds = cmd_callback.cmd
        elif help_flags and help_flags.get("cmds"):
            cmds = help_flags.get("cmds")

        if not cmds:
            continue

        only_admin = any(isinstance(f.callback, UserRestricting) for f in handler.filters)
        only_pm = any(
            isinstance(f.callback, ChatTypeFilter) and f.callback.chat_types == (ChatType.PRIVATE.value,)
            for f in handler.filters
        )
        only_chats = any(
            (
                (
                    isinstance(f.callback, ChatTypeFilter)
                    and set(f.callback.chat_types) == {ChatType.GROUP.value, ChatType.SUPERGROUP.value}
                )
                or (
                    isinstance(f.callback, _InvertFilter)
                    and isinstance(f.callback.target.callback, ChatTypeFilter)
                    and f.callback.target.callback.chat_types == (ChatType.PRIVATE.value,)
                )
            )
            for f in handler.filters
        )
        only_op = any(isinstance(f.callback, IsOP) for f in handler.filters)

        if help_flags and help_flags.get("args"):
            args = await gather_cmd_args(help_flags["args"])
        else:
            args = await gather_cmd_args(handler.flags.get("args"))

        disableable = handler.flags.get("disableable")
        disableable_name = disableable.name if disableable else None

        cmd_list = normalize_cmds(cmds)
        if not cmd_list:
            continue
        cmd = HandlerHelp(
            cmds=cmd_list,
            args=args,
            description=help_flags.get("description", "") if help_flags else "",
            only_admin=only_admin,
            only_op=only_op,
            only_pm=only_pm,
            only_chats=only_chats,
            alias_to_modules=help_flags.get("alias_to_modules", []) if help_flags else [],
            disableable=disableable_name,
            raw_cmds=bool(help_flags and help_flags.get("raw_cmds")),
        )
        helps.append(cmd)

        if disableable_name:
            DISABLEABLE_CMDS.append(cmd)

    await logger.adebug(
        f"gather_cmds_help: {router.name}", cmds=list(chain.from_iterable(mhelp.cmds for mhelp in helps))
    )
    return helps


async def gather_module_help(module: ModuleType) -> ModuleHelp | None:
    if not hasattr(module, "router"):
        return None

    name: LazyProxy | str = getattr(module, "__module_name__", module.__name__.split(".")[-1])
    emoji = getattr(module, "__module_emoji__", "?")
    exclude_public = getattr(module, "__exclude_public__", False)
    info = getattr(module, "__module_info__", None)
    description = getattr(module, "__module_description__", None)

    await logger.adebug(f"gather_module_help: {module.__name__}", name=name, emoji=emoji)

    if cmds := await gather_cmds_help(module.router):
        return ModuleHelp(
            handlers=cmds,
            name=name,
            icon=emoji,
            exclude_public=exclude_public,
            info=info or "",
            description=description or "",
        )
    return None
