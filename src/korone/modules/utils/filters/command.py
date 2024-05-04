# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

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
    """
    Represents an error that occurs during command processing.

    CommandError is a subclass of the `Exception` class. It is raised when an error occurs
    during command processing.
    """

    pass


@dataclass(frozen=True, slots=True)
class CommandObject:
    """
    Represents a command object.

    CommandObject is a dataclass that represents a command object. It contains the command prefix,
    name, mention, arguments, regular expression match object, and magic result. It is used by the
    :class:`Command` filter to store the command information. It also provides a method to parse
    the command from a message.
    """

    message: Message | None = field(repr=False, default=None)
    """The message object.

    :type: hydrogram.types.Message | None
    """
    prefix: str = "/"
    """The command prefix.

    :type: str
    """
    command: str = ""
    """The command name.

    :type: str
    """
    mention: str | None = None
    """The mention string.

    :type: str | None
    """
    args: str | None = field(repr=False, default=None)
    """"The command arguments.

    :type: str | None
    """
    regexp_match: re.Match[str] | None = field(repr=False, default=None)
    """The regular expression match object.

    :type: re.Match[str] | None
    """
    magic_result: Any | None = field(repr=False, default=None)
    """The magic result.

    :type: typing.Any | None
    """

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
        """
        Parse the command from the given message.

        Parses the command from the given message by extracting the command prefix, name, mention,
        and arguments. If the command is a regular expression, the regular expression match object
        is stored in the command object.

        Returns
        -------
        CommandObject
            The parsed command object.

        Raises
        ------
        CommandError
            If no message is provided.
        CommandError
            If the message has no text.
        """
        if not self.message:
            msg = "To parse a command, you need to pass a message."
            raise CommandError(msg)

        text = self.message.text or self.message.caption
        if not text:
            msg = "Message has no text"
            raise CommandError(msg)

        return self.__extract(text)


class Command(Filter):
    """
    A filter that matches specific commands in messages.

    The :class:`Command` class is a subclass of the `Filter` class. It provides functionality to
    match specific commands in messages. The class takes in various parameters such as `commands`,
    `prefix`, `ignore_case`, `ignore_mention`, and `magic` to customize the behavior of the filter.

    Parameters
    ----------
    *values : CommandPatternType
        Additional commands to match.
    commands : typing.Sequence[CommandPatternType] | CommandPatternType | None, optional
        Specific commands to match. Can be a single command or a sequence of commands.
    prefix : str, optional
        The prefix used before the command. Defaults to "/".
    ignore_case : bool, optional
        Whether to ignore the case when matching commands. Defaults to False.
    ignore_mention : bool, optional
        Whether to ignore mentions when matching commands. Defaults to False.
    magic : magic_filter.MagicFilter or None, optional
        A magic filter to apply to the command. Defaults to None.

    Raises
    ------
    ValueError
        If the commands parameter is not a valid type.
    """

    __slots__ = ("commands", "ignore_case", "ignore_mention", "magic", "prefix")

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        prefix: str = "/",
        ignore_case: bool = False,
        ignore_mention: bool = False,
        magic: MagicFilter | None = None,
    ):
        commands = [commands] if isinstance(commands, str | re.Pattern) else commands or []
        if not isinstance(commands, Iterable):
            msg = "Command filter only supports str, re.Pattern object or their Iterable"
            raise ValueError(msg)

        def process_command(command):
            if isinstance(command, str):
                command = re.compile(
                    re.escape(command.casefold() if ignore_case else command) + "$"
                )

            if not isinstance(command, re.Pattern):
                msg = "Command filter only supports str, re.Pattern, or their Iterable"
                raise ValueError(msg)

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

    async def __call__(self, client: Client, message: Message) -> bool:
        """
        Check if the message contains a valid command.

        Check if the message contains a valid command by calling the :meth:`parse_command` method.

        Parameters
        ----------
        client : hydrogram.Client
            The client instance.
        message : hydrogram.types.Message
            The message to check.

        Returns
        -------
        bool
            Returns True if a valid command is found, otherwise False.
        """
        if message.text or message.caption:
            with suppress(CommandError):
                await self.parse_command(client, message)
                return True

        return False

    def validate_prefix(self, command: CommandObject) -> None:
        """
        Validate the prefix of the command.

        Validate the prefix of the command by checking if it matches the prefix provided in the
        filter. If the prefix is invalid, a CommandError is raised.

        Parameters
        ----------
        command : CommandObject
            The command object to validate.

        Raises
        ------
        CommandError
            If the prefix is invalid.
        """
        if command.prefix != self.prefix:
            msg = f"Invalid prefix: {command.prefix!r}"
            raise CommandError(msg)

    async def validade_mention(self, client: Client, command: CommandObject) -> None:
        """
        Validate the mention in the command.

        Validate the mention in the command by checking if it matches the bot's username. If the
        mention is invalid, a CommandError is raised.

        Parameters
        ----------
        client : hydrogram.Client
            The client instance.
        command : CommandObject
            The command object to validate.

        Raises
        ------
        CommandError
            If the mention is invalid.
        """
        if command.mention and not self.ignore_mention:
            if not (me := client.me):
                me = await client.get_me()

            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}"
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        """
        Validate the command itself.

        Validate the command itself by checking if it matches any of the allowed commands. If the
        command is a regular expression, the regular expression match object is stored in the
        command object.

        Parameters
        ----------
        command : CommandObject
            The command object to validate.

        Returns
        -------
        CommandObject
            The validated command object.

        Raises
        ------
        CommandError
            If the command is invalid.
        """
        command_name = command.command.casefold() if self.ignore_case else command.command

        for allowed_command in self.commands:
            if isinstance(allowed_command, re.Pattern):
                result = allowed_command.match(command.command)
                if result:
                    return replace(command, regexp_match=result)

            if command_name == allowed_command:
                return command

        msg = f"Invalid command: {command.command!r}"
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        """
        Parse the command from the message and apply necessary validations.

        Parse the command from the message and apply the necessary validations such as prefix,
        mention, and command itself. If the command is valid, it applies the magic filter (if
        provided) to the command.

        Parameters
        ----------
        client : hydrogram.Client
            The client instance.
        message : hydrogram.types.Message
            The message to parse.

        Returns
        -------
        CommandObject
            The parsed and validated command object.

        Raises
        ------
        CommandError
            If the command is invalid or any validation fails.
        """
        command = CommandObject(message).parse()

        self.validate_prefix(command)
        await self.validade_mention(client, command)
        return self.do_magic(command=self.validate_command(command))

    def do_magic(self, command: CommandObject) -> CommandObject:
        """
        Apply the magic filter to the command.

        The magic filter is applied to the command if the magic filter is provided and the command
        is valid. If the command is rejected by the magic filter, a CommandError is raised.

        Parameters
        ----------
        command : CommandObject
            The command object to apply the magic filter to.

        Returns
        -------
        CommandObject
            The command object with the magic filter applied.

        Raises
        ------
        CommandError
            If the command is rejected by the magic filter.
        """
        if self.magic:
            result = self.magic.resolve(command)
            if not result:
                msg = "Rejected by magic filter"
                raise CommandError(msg)

            return replace(command, magic_result=result)

        return command
