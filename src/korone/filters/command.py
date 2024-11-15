# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field, replace
from re import Pattern
from typing import TYPE_CHECKING, Any, Final, Self

from hydrogram.filters import Filter

from korone.modules.core import COMMANDS

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message
    from magic_filter import MagicFilter

PREFIX: Final[str] = "/"
CommandPatternType = str | Pattern[str]


class CommandError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CommandObject:
    message: Message | None = field(repr=False, default=None)
    prefix: str = PREFIX
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
        return bool(command) and all(char.isalnum() or char.isspace() for char in command)

    def extract(self, text: str) -> Self:
        if not text.startswith(self.prefix):
            msg = f"Command must start with the prefix '{self.prefix}'."
            raise CommandError(msg)

        command_text = text[len(self.prefix) :].strip()
        if not command_text:
            msg = "No command found after the prefix."
            raise CommandError(msg)

        parts = command_text.split(maxsplit=1)
        full_command = parts[0]
        args = parts[1] if len(parts) > 1 else None

        command, _, mention = full_command.partition("@")

        if not self.is_valid_command(command):
            msg = (
                "Command contains invalid characters. "
                "Only alphanumeric characters and spaces are allowed."
            )
            raise CommandError(msg)

        return replace(self, command=command, mention=mention or None, args=args)

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
    __slots__ = ("commands", "disableable", "ignore_case", "ignore_mention", "magic", "prefix")

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        prefix: str = PREFIX,
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
        disableable: bool = True,
    ) -> None:
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic
        self.disableable = disableable
        self.commands = tuple(self._prepare_commands(values, commands, ignore_case))

        if not self.commands:
            msg = "Command filter requires at least one command."
            raise ValueError(msg)

    def _prepare_commands(
        self,
        values: Iterable[CommandPatternType],
        commands: Sequence[CommandPatternType] | CommandPatternType | None,
        ignore_case: bool,
    ) -> Iterable[Pattern[str]]:
        if isinstance(commands, str | Pattern):
            commands = [commands]
        elif commands is None:
            commands = []

        if not isinstance(commands, Iterable):
            msg = "Command filter only supports str, Pattern objects or their iterable."
            raise TypeError(msg)

        combined_commands = list(values) + list(commands)
        return [self._process_command(command, ignore_case) for command in combined_commands]

    @staticmethod
    def _process_command(command: CommandPatternType, ignore_case: bool) -> Pattern[str]:
        if isinstance(command, str):
            command_str = command.lower() if ignore_case else command
            pattern = re.escape(command_str) + r"$"
            return re.compile(pattern)
        if not isinstance(command, Pattern):
            msg = "Command filter only supports str or Pattern objects."
            raise TypeError(msg)
        return command

    async def __call__(self, client: Client, message: Message) -> bool:
        if not (message.text or message.caption):
            return False

        with suppress(CommandError):
            await self.parse_command(client, message)
            return True
        return False

    def validate_prefix(self, command: CommandObject) -> None:
        if command.prefix != self.prefix:
            msg = f"Invalid prefix: {command.prefix!r}."
            raise CommandError(msg)

    async def validate_mention(self, client: Client, command: CommandObject) -> None:
        if command.mention and not self.ignore_mention:
            me = client.me or await client.get_me()
            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}."
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        command_name = command.command.lower() if self.ignore_case else command.command

        for allowed_command in self.commands:
            if match := allowed_command.match(command.command):
                return replace(command, regexp_match=match)
            if command_name == allowed_command.pattern.rstrip("$"):
                return command

        msg = f"Invalid command: {command.command!r}."
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        command = CommandObject(message=message).parse()
        self.validate_prefix(command)
        await self.validate_mention(client, command)

        command_name = command.command
        if self.disableable and command_name in COMMANDS:
            chat_id = message.chat.id
            parent_command = COMMANDS[command_name].get("parent", command_name)
            if not COMMANDS[parent_command]["chat"].get(chat_id, True):
                msg = f"Command '{command_name}' is disabled in chat '{chat_id}'."
                raise CommandError(msg)

        validated_command = self.validate_command(command)
        return self.do_magic(validated_command)

    def do_magic(self, command: CommandObject) -> CommandObject:
        if self.magic:
            if result := self.magic.resolve(command):
                return replace(command, magic_result=result)
            msg = "Rejected by magic filter."
            raise CommandError(msg)
        return command
