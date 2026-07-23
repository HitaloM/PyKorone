from dataclasses import dataclass
from re import compile as compile_pattern
from typing import TYPE_CHECKING, Final

from aiogram.types import (
    BotCommand,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeUnion,
)

from korone.logger import get_logger
from korone.modules.help.utils.extract_info import HELP_MODULES, HandlerHelp

if TYPE_CHECKING:
    from collections.abc import Iterator

    from aiogram import Bot

    from korone.utils.i18n import I18nNew

MAX_BOT_COMMANDS: Final[int] = 100
MAX_COMMAND_DESCRIPTION_LENGTH: Final[int] = 256
EPHEMERAL_GROUP_COMMANDS: Final[frozenset[str]] = frozenset({"help"})
BOT_COMMAND_PATTERN = compile_pattern(r"[a-z0-9_]{1,32}")

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class CommandScopeConfig:
    scope: BotCommandScopeUnion
    include_groups: bool
    include_admin_commands: bool


COMMAND_SCOPES: Final[tuple[CommandScopeConfig, ...]] = (
    CommandScopeConfig(scope=BotCommandScopeAllPrivateChats(), include_groups=False, include_admin_commands=True),
    CommandScopeConfig(scope=BotCommandScopeAllGroupChats(), include_groups=True, include_admin_commands=False),
    CommandScopeConfig(scope=BotCommandScopeAllChatAdministrators(), include_groups=True, include_admin_commands=True),
)


def _is_available(handler: HandlerHelp, config: CommandScopeConfig) -> bool:
    if handler.only_op or handler.raw_cmds:
        return False
    if config.include_groups and handler.only_pm:
        return False
    if not config.include_groups and handler.only_chats:
        return False
    return config.include_admin_commands or not handler.only_admin


def _iter_scope_handlers(config: CommandScopeConfig) -> Iterator[HandlerHelp]:
    for module in HELP_MODULES.values():
        if module.exclude_public:
            continue
        for handler in module.handlers:
            if _is_available(handler, config):
                yield handler


def build_bot_commands(config: CommandScopeConfig) -> list[BotCommand]:
    commands: list[BotCommand] = []
    seen_commands: set[str] = set()

    for handler in _iter_scope_handlers(config):
        command = handler.cmds[0]
        if command in seen_commands or handler.description is None:
            continue
        if BOT_COMMAND_PATTERN.fullmatch(command) is None:
            msg = f"Invalid Telegram bot command: {command!r}"
            raise ValueError(msg)

        description = str(handler.description).strip()
        if not description:
            continue

        commands.append(
            BotCommand(
                command=command,
                description=description[:MAX_COMMAND_DESCRIPTION_LENGTH],
                is_ephemeral=True if config.include_groups and command in EPHEMERAL_GROUP_COMMANDS else None,
            )
        )
        seen_commands.add(command)

    if len(commands) > MAX_BOT_COMMANDS:
        msg = f"Telegram supports at most {MAX_BOT_COMMANDS} commands per scope, got {len(commands)}"
        raise ValueError(msg)
    return commands


def _iter_command_locales(i18n: I18nNew) -> Iterator[tuple[str | None, str]]:
    yield None, i18n.default_locale

    seen_language_codes: set[str] = set()
    for locale in i18n.available_locales:
        language_code = i18n.to_iso_639_1(locale)
        if language_code in seen_language_codes:
            continue
        seen_language_codes.add(language_code)
        yield language_code, locale


async def sync_bot_commands(bot: Bot, i18n: I18nNew) -> None:
    for language_code, locale in _iter_command_locales(i18n):
        with i18n.use_locale(locale):
            for config in COMMAND_SCOPES:
                commands = build_bot_commands(config)
                await bot.set_my_commands(commands=commands, scope=config.scope, language_code=language_code)
                await logger.adebug(
                    "Bot commands synchronized",
                    scope=config.scope.type,
                    language_code=language_code,
                    count=len(commands),
                )
