# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

from hydrogram.filters import Filter

from korone.modules import COMMANDS

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message
    from magic_filter import MagicFilter

CommandPatternType = str | re.Pattern


class CommandError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CommandObject:
    message: Message | None = field(repr=False, default=None)
    prefix: str = "/"
    command: str = ""
    mention: str | None = None
    args: str | None = field(repr=False, default=None)
    regexp_match: re.Match[str] | None = field(repr=False, default=None)
    magic_result: Any = field(repr=False, default=None)

    @staticmethod
    def extract(text: str) -> CommandObject:
        try:
            full_command, *args = text.split(maxsplit=1)
        except ValueError as e:
            msg = "Not enough values to unpack."
            raise CommandError(msg) from e

        prefix = full_command[0]
        command, _, mention = full_command[1:].partition("@")
        return CommandObject(
            prefix=prefix,
            command=command,
            mention=mention or None,
            args=args[0] if args else None,
        )

    def parse(self) -> CommandObject:
        if not self.message:
            msg = "Message is required to parse a command."
            raise CommandError(msg)

        text = self.message.text or self.message.caption
        if not text:
            msg = "Message has no text"
            raise CommandError(msg)

        return self.extract(text)


class Command(Filter):
    __slots__ = ("commands", "disableable", "ignore_case", "ignore_mention", "magic", "prefix")

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        prefix: str = "/",
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
        disableable: bool = True,
    ) -> None:
        commands = self._prepare_commands(values, commands, ignore_case)
        if not commands:
            msg = "Command filter requires at least one command"
            raise ValueError(msg)

        self.commands = tuple(commands)
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic
        self.disableable = disableable

    def _prepare_commands(self, values, commands, ignore_case):
        if isinstance(commands, str | re.Pattern):
            commands = [commands]
        elif commands is None:
            commands = []

        if not isinstance(commands, Iterable):
            msg = "Command filter only supports str, re.Pattern object or their Iterable"
            raise TypeError(msg)

        return [self._process_command(command, ignore_case) for command in (*values, *commands)]

    @staticmethod
    def _process_command(command, ignore_case):
        if isinstance(command, str):
            command = re.compile(re.escape(command.casefold() if ignore_case else command) + "$")
        if not isinstance(command, re.Pattern):
            msg = "Command filter only supports str, re.Pattern object or their Iterable"
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
            msg = f"Invalid prefix: {command.prefix!r}"
            raise CommandError(msg)

    async def validate_mention(self, client: Client, command: CommandObject) -> None:
        if command.mention and not self.ignore_mention:
            me = client.me or await client.get_me()
            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}"
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        command_name = command.command.casefold() if self.ignore_case else command.command

        for allowed_command in self.commands:
            if isinstance(allowed_command, re.Pattern):
                if result := allowed_command.match(command.command):
                    return replace(command, regexp_match=result)
            elif command_name == allowed_command:
                return command

        msg = f"Invalid command: {command.command!r}"
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        command = CommandObject(message).parse()
        self.validate_prefix(command)
        await self.validate_mention(client, command)

        command_name = command.command
        if self.disableable and command_name in COMMANDS:
            chat_id = message.chat.id
            command_name = COMMANDS[command_name].get("parent", command_name)
            if not COMMANDS[command_name]["chat"].get(chat_id, True):
                msg = f"Command {command_name} is disabled in '{chat_id}'."
                raise CommandError(msg)

        return self.do_magic(self.validate_command(command))

    def do_magic(self, command: CommandObject) -> CommandObject:
        if self.magic:
            result = self.magic.resolve(command)
            if result:
                return replace(command, magic_result=result)
            msg = "Rejected by magic filter"
            raise CommandError(msg)
        return command
