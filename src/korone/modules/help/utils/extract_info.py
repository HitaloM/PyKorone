from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, cast

from aiogram.dispatcher.flags import extract_flags
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import GroupChatFilter, PrivateChatFilter
from korone.filters.user_status import IsOP
from korone.logger import get_logger

if TYPE_CHECKING:
    from aiogram import Router
    from babel.support import LazyProxy

    from korone.modules.metadata import LoadedModule
    from korone.ui import Text, UIExpression

type HelpFlags = Mapping[str, object]
type HelpExample = tuple[object | None, str]

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class HandlerHelp:
    cmds: tuple[str, ...]
    args: ArgumentSchema[object] | None
    description: LazyProxy | str | None
    examples: tuple[HelpExample, ...]
    only_admin: bool
    only_op: bool
    only_pm: bool
    only_chats: bool
    alias_to_modules: tuple[str, ...]
    disableable: str | None
    raw_cmds: bool


@dataclass(slots=True, kw_only=True)
class ModuleHelp:
    handlers: list[HandlerHelp]
    name: LazyProxy | str
    icon: str
    exclude_public: bool
    info: str | LazyProxy | Text | UIExpression
    description: str | LazyProxy | Text | UIExpression


HELP_MODULES: OrderedDict[str, ModuleHelp] = OrderedDict()
DISABLEABLE_CMDS: list[HandlerHelp] = []
HELP_CMD_INDEX: dict[str, HandlerHelp] = {}


def reset_help_registry() -> None:
    HELP_MODULES.clear()
    DISABLEABLE_CMDS.clear()
    HELP_CMD_INDEX.clear()


def register_handler_help(handler_help: HandlerHelp) -> None:
    if handler_help.disableable:
        DISABLEABLE_CMDS.append(handler_help)

    for cmd in handler_help.cmds:
        HELP_CMD_INDEX.setdefault(cmd, handler_help)


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


def get_cmd_help_by_name(name: str) -> HandlerHelp | None:
    return HELP_CMD_INDEX.get(name)


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


def gather_cmd_args(args: object) -> ArgumentSchema[object] | None:
    if args is None:
        return None

    if isinstance(args, ArgumentSchema):
        return cast("ArgumentSchema[object]", args)

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

    return only_admin, only_op, only_pm, only_chats


def _extract_args(flags: Mapping[str, object], help_flags: HelpFlags) -> ArgumentSchema[object] | None:
    args_source = help_flags["args"] if "args" in help_flags else flags.get("args")
    return gather_cmd_args(args_source)


def _normalize_example(value: object) -> HelpExample | None:
    if isinstance(value, str):
        return None, value

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) == 2:
        label, example = value
        if isinstance(example, str):
            return label, example

    return None


def _extract_examples(help_flags: HelpFlags) -> tuple[HelpExample, ...]:
    examples = help_flags.get("examples")
    if isinstance(examples, str):
        return ((None, examples),)

    if isinstance(examples, Sequence) and not isinstance(examples, (str, bytes)):
        normalized_examples: list[HelpExample] = []
        for example in examples:
            normalized_example = _normalize_example(example)
            if normalized_example is not None:
                normalized_examples.append(normalized_example)

        if normalized_examples:
            return tuple(normalized_examples)

    return ()


async def gather_cmds_help(router: Router) -> list[HandlerHelp]:
    helps: list[HandlerHelp] = []

    for sub_router in router.sub_routers:
        helps.extend(await gather_cmds_help(sub_router))

    for handler in router.message.handlers:
        if not handler.filters:
            continue

        handler_flags = extract_flags(handler)
        help_flags = _get_help_flags(handler_flags)
        if bool(help_flags.get("exclude")):
            continue

        cmd_list = _extract_cmds(handler.filters, handler_flags, help_flags)
        if not cmd_list:
            continue

        only_admin, only_op, only_pm, only_chats = _extract_visibility_flags(handler.filters)
        args = _extract_args(handler_flags, help_flags)
        examples = _extract_examples(help_flags)

        disableable = handler_flags.get("disableable")
        disableable_name = disableable.name if disableable is not None else None
        description = cast("LazyProxy | str | None", help_flags.get("description"))
        alias_to_modules = _normalize_str_sequence(help_flags.get("alias_to_modules")) or ()

        handler_help = HandlerHelp(
            cmds=cmd_list,
            args=args,
            description=description,
            examples=examples,
            only_admin=only_admin,
            only_op=only_op,
            only_pm=only_pm,
            only_chats=only_chats,
            alias_to_modules=alias_to_modules,
            disableable=disableable_name,
            raw_cmds=bool(help_flags.get("raw_cmds")),
        )
        helps.append(handler_help)
        register_handler_help(handler_help)

    await logger.adebug(
        "gather_cmds_help", router=router.name, cmds=list(chain.from_iterable(handler.cmds for handler in helps))
    )
    return helps


async def gather_module_help(module: LoadedModule) -> ModuleHelp | None:
    router = module.router
    if router is None:
        return None

    package = module.package
    name = package.name
    info = package.description
    description = package.summary

    await logger.adebug("gather_module_help", module=module.import_path, name=name, emoji=package.icon)

    if cmds := await gather_cmds_help(router):
        return ModuleHelp(
            handlers=cmds,
            name=name or "N/A",
            icon=package.icon,
            exclude_public=not package.public,
            info=info if info is not None else "",
            description=description if description is not None else "",
        )
    return None
