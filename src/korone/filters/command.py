# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from re import Pattern
from typing import TYPE_CHECKING, Any, Final, Self

from hydrogram.filters import Filter

from korone.modules.core import COMMANDS

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message
    from magic_filter import MagicFilter

PREFIXES: Final[tuple[str, ...]] = ("/", "!")
CommandPatternType = str | Pattern[str]


class CommandError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CommandObject:
    message: Message | None = field(repr=False, default=None)
    prefix: str = ""
    command: str = ""
    mention: str | None = None
    args: str | None = field(repr=False, default=None)
    regexp_match: re.Match[str] | None = field(repr=False, default=None)
    magic_result: Any = field(repr=False, default=None)

    def __str__(self) -> str:
        return (
            f"Command(prefix={self.prefix!r}, command={self.command!r}, mention={self.mention!r})"
        )

    @staticmethod
    def is_valid_command(command: str) -> bool:
        return bool(command) and command.replace(" ", "").isalnum()

    def extract(self, text: str) -> Self:
        prefix = next((p for p in PREFIXES if text.startswith(p)), None)
        if not prefix:
            msg = f"Command must start with one of the prefixes {PREFIXES}."
            raise CommandError(msg)

        command_text = text[len(prefix) :].strip()
        if not command_text:
            msg = "No command found after the prefix."
            raise CommandError(msg)

        parts = command_text.split(maxsplit=1)
        full_command, args = parts[0], parts[1] if len(parts) > 1 else None
        command, _, mention = full_command.partition("@")

        if not self.is_valid_command(command):
            msg = (
                "Command contains invalid characters. Only alphanumeric "
                "characters and spaces are allowed."
            )
            raise CommandError(msg)

        return replace(self, prefix=prefix, command=command, mention=mention or None, args=args)

    def parse(self) -> Self:
        if not self.message:
            msg = "Message is required to parse a command."
            raise CommandError(msg)

        text = self.message.text or self.message.caption
        if not text:
            msg = "Message has no text."
            raise CommandError(msg)

        return self.extract(text)


class Command(Filter):
    __slots__ = ("commands", "disableable", "ignore_case", "ignore_mention", "magic", "prefixes")

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        prefixes: tuple[str, ...] = PREFIXES,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
        disableable: bool = True,
    ) -> None:
        self.prefixes = prefixes
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic
        self.disableable = disableable
        self.commands = tuple(self._prepare_commands(values, commands))

        if not self.commands:
            msg = "Command filter requires at least one command."
            raise ValueError(msg)

    def _prepare_commands(
        self,
        values: Iterable[CommandPatternType],
        commands: Sequence[CommandPatternType] | CommandPatternType | None,
    ) -> Iterable[Pattern[str]]:
        cmds = list(values)
        if commands:
            cmds.extend(commands if isinstance(commands, Iterable) else [commands])
        return (self._compile_command(cmd) for cmd in cmds)

    def _compile_command(self, command: CommandPatternType) -> Pattern[str]:
        if isinstance(command, str):
            cmd = command.lower() if self.ignore_case else command
            return re.compile(re.escape(cmd) + r"$")
        if isinstance(command, Pattern):
            return command
        msg = "Command filter only supports str or Pattern objects."
        raise TypeError(msg)

    async def __call__(self, client: Client, message: Message) -> bool:
        if not (message.text or message.caption):
            return False

        try:
            await self.parse_command(client, message)
            return True
        except CommandError:
            return False

    def validate_prefix(self, command: CommandObject) -> None:
        prefix = command.prefix.lower() if self.ignore_case and command.prefix else command.prefix
        valid_prefixes = [p.lower() for p in self.prefixes] if self.ignore_case else self.prefixes
        if prefix not in valid_prefixes:
            msg = f"Invalid prefix: {command.prefix!r}."
            raise CommandError(msg)

    async def validate_mention(self, client: Client, command: CommandObject) -> None:
        if command.mention and not self.ignore_mention:
            me = client.me or await client.get_me()
            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}."
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        cmd_name = command.command.lower() if self.ignore_case else command.command
        for allowed_cmd in self.commands:
            match = allowed_cmd.match(cmd_name)
            if match:
                return replace(command, regexp_match=match)
        msg = f"Invalid command: {command.command!r}."
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        command = CommandObject(message=message).parse()
        self.validate_prefix(command)
        await self.validate_mention(client, command)

        if self.disableable and command.command in COMMANDS:
            chat_id = message.chat.id
            parent = COMMANDS[command.command].get("parent", command.command)
            if not COMMANDS[parent]["chat"].get(chat_id, True):
                msg = f"Command '{command.command}' is disabled in chat '{chat_id}'."
                raise CommandError(msg)

        validated_command = self.validate_command(command)
        return self._apply_magic(validated_command)

    def _apply_magic(self, command: CommandObject) -> CommandObject:
        if self.magic:
            result = self.magic.resolve(command)
            if result:
                return replace(command, magic_result=result)
            msg = "Rejected by magic filter."
            raise CommandError(msg)
        return command
