from __future__ import annotations

from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from inspect import isawaitable
from itertools import chain
from typing import TYPE_CHECKING, Any, cast

from aiogram.filters import Command
from aiogram.filters.logic import _InvertFilter
from aiogram.types import Message
from ass_tg.types.base_abc import ArgFabric
from ass_tg.types.logic import OptionalArg

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import GroupChatFilter, PrivateChatFilter
from korone.filters.user_status import IsOP
from korone.logger import get_logger
from korone.utils.i18n import LazyProxy as KoroneLazyProxy

if TYPE_CHECKING:
    from types import ModuleType

    from aiogram import Router
    from babel.support import LazyProxy
    from stfu_tg import Doc

type ArgsMap = dict[str, ArgFabric]
type ArgsProvider = Callable[[Message | None, dict[str, Any]], ArgsMap | Awaitable[ArgsMap]]
type ArgsSource = ArgsMap | ArgsProvider | None
type HelpFlags = Mapping[str, object]

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class HandlerHelp:
    cmds: tuple[str, ...]
    args: ArgsMap | None
    description: LazyProxy | str | None
    only_admin: bool
    only_op: bool
    only_pm: bool
    only_chats: bool
    alias_to_modules: tuple[str, ...]
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
    return {
        mod_name: handlers
        for mod_name, module in HELP_MODULES.items()
        if (
            handlers := [cmd for cmd in module.handlers if cmd.alias_to_modules and module_name in cmd.alias_to_modules]
        )
    }


def get_all_cmds() -> list[HandlerHelp]:
    return list(chain.from_iterable(module.handlers for module in HELP_MODULES.values()))


def get_all_cmds_raw() -> tuple[str, ...]:
    return tuple(chain.from_iterable(cmds.cmds for cmds in get_all_cmds()))


def _normalize_str_sequence(values: object) -> tuple[str, ...] | None:
    if isinstance(values, str):
        return (values,)
    if (
        isinstance(values, Sequence)
        and not isinstance(values, (str, bytes))
        and all(isinstance(v, str) for v in values)
    ):
        return tuple(values)
    return None


def normalize_cmds(cmds: object) -> tuple[str, ...] | None:
    return _normalize_str_sequence(cmds)


def _clone_without_cache(description: LazyProxy | str | None) -> LazyProxy | str | None:
    if not isinstance(description, KoroneLazyProxy):
        return description
    return KoroneLazyProxy(description._func, *description._args, enable_cache=False, **description._kwargs)


def _normalize_arg_description(fabric: ArgFabric) -> ArgFabric:
    description = _clone_without_cache(fabric.description)
    if isinstance(fabric, OptionalArg):
        if description is not None:
            fabric.description = KoroneLazyProxy(lambda d=description: f"?{d}", enable_cache=False)
        return fabric
    fabric.description = description
    return fabric


def _prepare_args(args: Mapping[str, ArgFabric]) -> ArgsMap:
    normalized: ArgsMap = {}
    for arg_name, fabric in args.items():
        try:
            normalized[arg_name] = _normalize_arg_description(fabric)
        except TypeError:
            normalized[arg_name] = fabric
    return normalized


async def gather_cmd_args(args: ArgsSource) -> ArgsMap | None:
    if args is None:
        return None

    if isinstance(args, Mapping):
        return _prepare_args(args)

    if callable(args):
        result = args(None, {})
        if isawaitable(result):
            result = await cast("Awaitable[ArgsMap]", result)
        if isinstance(result, Mapping):
            return _prepare_args(result)

        msg = f"Unsupported args provider return type: {type(result)!r}"
        raise TypeError(msg)

    msg = "Unsupported args type"
    raise TypeError(msg)


def _get_help_flags(flags: Mapping[str, object]) -> HelpFlags:
    help_flags = flags.get("help")
    if isinstance(help_flags, Mapping):
        return cast("HelpFlags", help_flags)
    return {}


def _extract_cmds_from_command_filters(command_filters: Sequence[object]) -> tuple[str, ...] | None:
    cmds: list[str] = []
    for command_filter in command_filters:
        if not isinstance(command_filter, Command):
            continue
        cmds.extend(command for command in command_filter.commands if isinstance(command, str))
    if not cmds:
        return None
    return tuple(dict.fromkeys(cmds))


def _extract_cmds(filters: Sequence[Any], flags: Mapping[str, object], help_flags: HelpFlags) -> tuple[str, ...] | None:
    if "cmds" in help_flags:
        return normalize_cmds(help_flags["cmds"])

    command_flags = flags.get("commands")
    if isinstance(command_flags, Sequence) and (cmd_list := _extract_cmds_from_command_filters(command_flags)):
        return cmd_list

    for handler_filter in filters:
        callback = getattr(handler_filter, "callback", None)
        if isinstance(callback, Command) and (cmd_list := _extract_cmds_from_command_filters((callback,))):
            return cmd_list

    return None


def _extract_visibility_flags(filters: Sequence[Any]) -> tuple[bool, bool, bool, bool]:
    only_admin = False
    only_op = False
    only_pm = False
    only_chats = False

    for handler_filter in filters:
        callback = getattr(handler_filter, "callback", None)

        if isinstance(callback, UserRestricting):
            only_admin = True
        if isinstance(callback, IsOP):
            only_op = True
        if isinstance(callback, PrivateChatFilter):
            only_pm = True
        if isinstance(callback, GroupChatFilter):
            only_chats = True
        if isinstance(callback, _InvertFilter):
            target_callback = getattr(getattr(callback, "target", None), "callback", None)
            if isinstance(target_callback, PrivateChatFilter):
                only_chats = True
            if isinstance(target_callback, GroupChatFilter):
                only_pm = True

    return only_admin, only_op, only_pm, only_chats


async def _extract_args(flags: Mapping[str, object], help_flags: HelpFlags) -> ArgsMap | None:
    args_source = help_flags["args"] if "args" in help_flags else flags.get("args")
    return await gather_cmd_args(cast("ArgsSource", args_source))


async def gather_cmds_help(router: Router) -> list[HandlerHelp]:
    helps: list[HandlerHelp] = []

    for sub_router in router.sub_routers:
        helps.extend(await gather_cmds_help(sub_router))

    for handler in router.message.handlers:
        if not handler.filters:
            continue

        help_flags = _get_help_flags(handler.flags)
        if bool(help_flags.get("exclude")):
            continue

        cmd_list = _extract_cmds(handler.filters, handler.flags, help_flags)
        if not cmd_list:
            continue

        only_admin, only_op, only_pm, only_chats = _extract_visibility_flags(handler.filters)
        args = await _extract_args(handler.flags, help_flags)

        disableable = handler.flags.get("disableable")
        disableable_name = disableable.name if disableable is not None else None
        description = _clone_without_cache(cast("LazyProxy | str | None", help_flags.get("description")))
        alias_to_modules = _normalize_str_sequence(help_flags.get("alias_to_modules")) or ()

        handler_help = HandlerHelp(
            cmds=cmd_list,
            args=args,
            description=description,
            only_admin=only_admin,
            only_op=only_op,
            only_pm=only_pm,
            only_chats=only_chats,
            alias_to_modules=alias_to_modules,
            disableable=disableable_name,
            raw_cmds=bool(help_flags.get("raw_cmds")),
        )
        helps.append(handler_help)

        if disableable_name:
            DISABLEABLE_CMDS.append(handler_help)

    await logger.adebug(
        "gather_cmds_help", router=router.name, cmds=list(chain.from_iterable(handler.cmds for handler in helps))
    )
    return helps


async def gather_module_help(module: ModuleType) -> ModuleHelp | None:
    router = getattr(module, "router", None)
    if router is None:
        return None

    name = _clone_without_cache(getattr(module, "__module_name__", module.__name__.split(".")[-1]))
    emoji = getattr(module, "__module_emoji__", "?")
    exclude_public = getattr(module, "__exclude_public__", False)
    info = _clone_without_cache(getattr(module, "__module_info__", None))
    description = _clone_without_cache(getattr(module, "__module_description__", None))

    await logger.adebug("gather_module_help", module=module.__name__, name=name, emoji=emoji)

    if cmds := await gather_cmds_help(router):
        return ModuleHelp(
            handlers=cmds,
            name=name or "N/A",
            icon=emoji,
            exclude_public=exclude_public,
            info=info if info is not None else "",
            description=description if description is not None else "",
        )
    return None
