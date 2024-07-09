# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field, replace
from typing import Any

from hydrogram import Client
from hydrogram.filters import Filter
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
    magic_result: Any | None = field(repr=False, default=None)

    @staticmethod
    def __extract(text: str) -> "CommandObject":
        try:
            full_command, *args = text.split(maxsplit=1)
        except ValueError as err:
            msg = "Not enough values to unpack."
            raise CommandError(msg) from err

        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
        return CommandObject(
            prefix=prefix,
            command=command,
            mention=mention or None,
            args=args[0] if args else None,
        )

    def parse(self) -> "CommandObject":
        if not self.message:
            msg = "Message is required to parse a command."
            raise CommandError(msg)

        if text := self.message.text or self.message.caption:
            return self.__extract(text)
        msg = "Message has no text"
        raise CommandError(msg)


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
        commands = [commands] if isinstance(commands, str | re.Pattern) else (commands or [])
        if not isinstance(commands, Iterable):
            msg = "Command filter only supports str, re.Pattern object or their Iterable"
            raise TypeError(msg)

        def process_command(command):
            if isinstance(command, str):
                command = re.compile(
                    f"{re.escape(command.casefold() if ignore_case else command)}$"
                )
            if not isinstance(command, re.Pattern):
                msg = "Command filter only supports str, re.Pattern object or their Iterable"
                raise TypeError(msg)
            return command

        items = [process_command(command) for command in (*values, *commands)]
        if not items:
            msg = "Command filter requires at least one command"
            raise ValueError(msg)

        self.commands = tuple(items)
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic
        self.disableable = disableable

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
            if not (me := client.me):
                me = await client.get_me()
            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}"
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        command_name = command.command.casefold() if self.ignore_case else command.command

        for allowed_command in self.commands:
            if isinstance(allowed_command, re.Pattern) and (
                result := allowed_command.match(command.command)
            ):
                return replace(command, regexp_match=result)
            if command_name == allowed_command:
                return command

        msg = f"Invalid command: {command.command!r}"
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        from korone.modules import COMMANDS  # noqa: PLC0415

        command = CommandObject(message).parse()

        self.validate_prefix(command)
        await self.validate_mention(client, command)

        command_name = command.command

        if self.disableable and command_name in COMMANDS:
            command_name = COMMANDS[command_name].get("parent", command_name)
            if (
                message.chat.id in COMMANDS[command_name].get("chat", {})
                and not COMMANDS[command_name]["chat"][message.chat.id]
            ):
                msg = f"Command {command_name} is disabled in '{message.chat.id}'."
                raise CommandError(msg)

        return self.do_magic(self.validate_command(command))

    def do_magic(self, command: CommandObject) -> CommandObject:
        if self.magic:
            if result := self.magic.resolve(command):
                return replace(command, magic_result=result)
            msg = "Rejected by magic filter"
            raise CommandError(msg)
        return command
