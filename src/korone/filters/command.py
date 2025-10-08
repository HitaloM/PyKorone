# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

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
    """Exception raised when a command cannot be parsed or is invalid."""

    pass


@dataclass(frozen=True, slots=True)
class CommandObject:
    """Object representing a parsed command.

    This immutable dataclass holds all relevant information extracted from
    a command message, such as the prefix used, command name, bot mention,
    and any arguments provided.

    Attributes:
        message: Original message that contains the command
        prefix: The command prefix used (e.g., '/', '!)
        command: The actual command name without prefix or mention
        mention: Optional mention part after the command (e.g., @bot_username)
        args: Arguments provided after the command, if any
        regexp_match: Match object if command was matched via regex
        magic_result: Result of applying a magic filter, if any
    """

    message: Message | None = field(repr=False, default=None)
    prefix: str = ""
    command: str = ""
    mention: str | None = None
    args: str | None = field(repr=False, default=None)
    regexp_match: re.Match[str] | None = field(repr=False, default=None)
    magic_result: Any = field(repr=False, default=None)

    def __str__(self) -> str:
        """Return string representation of the command object.

        Returns:
            str: Formatted representation of command details
        """
        return (
            f"Command(prefix={self.prefix!r}, command={self.command!r}, mention={self.mention!r})"
        )

    @staticmethod
    def is_valid_command(command: str) -> bool:
        """Check if a command name is valid.

        A valid command contains only alphanumeric characters and spaces.

        Args:
            command: The command name to validate

        Returns:
            bool: True if the command is valid, False otherwise
        """
        return bool(command) and command.replace(" ", "").isalnum()

    def extract(self, text: str) -> Self:
        """Extract command components from message text.

        This method parses the message text to extract the command prefix,
        the command itself, any mention, and arguments.

        Args:
            text: The message text to parse

        Returns:
            Self: A new CommandObject with the extracted components

        Raises:
            CommandError: If the text doesn't contain a valid command or prefix
        """
        # Find the first valid prefix in the text
        prefix = next((p for p in PREFIXES if text.startswith(p)), None)
        if not prefix:
            msg = f"Command must start with one of the prefixes {PREFIXES}."
            raise CommandError(msg)

        # Extract the command text (everything after the prefix)
        command_text = text[len(prefix) :].strip()
        if not command_text:
            msg = "No command found after the prefix."
            raise CommandError(msg)

        # Split into command and arguments
        parts = command_text.split(maxsplit=1)
        full_command, args = parts[0], parts[1] if len(parts) > 1 else None

        # Extract the command name and any mention
        command, _, mention = full_command.partition("@")

        if not self.is_valid_command(command):
            msg = (
                "Command contains invalid characters. Only alphanumeric "
                "characters and spaces are allowed."
            )
            raise CommandError(msg)

        # Return a new CommandObject with the extracted components
        return replace(self, prefix=prefix, command=command, mention=mention or None, args=args)

    def parse(self) -> Self:
        """Parse the command from the attached message.

        This method extracts command components from the message text or caption.

        Returns:
            Self: A new CommandObject with the extracted components

        Raises:
            CommandError: If there's no message or valid text to parse
        """
        if not self.message:
            msg = "Message is required to parse a command."
            raise CommandError(msg)

        text = self.message.text or self.message.caption
        if not text:
            msg = "Message has no text."
            raise CommandError(msg)

        return self.extract(text)


class Command(Filter):
    """Filter for matching bot commands.

    This filter checks if a message contains a valid command that matches
    any of the provided command patterns. It supports customization of
    prefixes, case sensitivity, and mention requirements.

    Attributes:
        command_patterns: Compiled patterns of allowed commands
        command_prefixes: Command prefixes to recognize
        ignore_case: Whether to ignore case when matching commands
        ignore_mention: Whether to ignore bot mentions after commands
        magic: Optional magic filter to further restrict command matches
        disableable: Whether this command can be disabled in specific chats
    """

    __slots__ = (
        "command_patterns",
        "command_prefixes",
        "disableable",
        "ignore_case",
        "ignore_mention",
        "magic",
    )

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
        """Initialize the command filter.

        Args:
            *values: Variable length command patterns
            commands: Additional command patterns as a sequence or single pattern
            prefixes: Valid command prefixes to recognize
            ignore_case: Whether to ignore case when matching commands
            ignore_mention: Whether to ignore bot mentions after commands
            magic: Optional magic filter to further filter commands
            disableable: Whether this command can be disabled in specific chats

        Raises:
            ValueError: If no command patterns are provided
        """
        self.command_prefixes = prefixes
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.magic = magic
        self.disableable = disableable
        self.command_patterns = tuple(self._prepare_commands(values, commands))

        if not self.command_patterns:
            msg = "Command filter requires at least one command."
            raise ValueError(msg)

    def _prepare_commands(
        self,
        values: Iterable[CommandPatternType],
        commands: Sequence[CommandPatternType] | CommandPatternType | None,
    ) -> Iterable[Pattern[str]]:
        """Prepare command patterns for matching.

        This method processes all provided command patterns and compiles them
        into regex Pattern objects.

        Args:
            values: Commands passed as positional arguments
            commands: Commands passed via the commands parameter

        Returns:
            Iterable[Pattern[str]]: Iterable of compiled regex patterns
        """
        cmds = list(values)
        if commands:
            cmds.extend(commands if isinstance(commands, Iterable) else [commands])
        return (self._compile_command(cmd) for cmd in cmds)

    def _compile_command(self, command: CommandPatternType) -> Pattern[str]:
        """Compile a command pattern into a regex Pattern.

        Args:
            command: The command pattern to compile

        Returns:
            Pattern[str]: Compiled regex pattern

        Raises:
            TypeError: If the command is not of a supported type
        """
        if isinstance(command, str):
            cmd = command.lower() if self.ignore_case else command
            return re.compile(re.escape(cmd) + r"$")
        if isinstance(command, Pattern):
            return command
        msg = "Command filter only supports str or Pattern objects."
        raise TypeError(msg)

    async def __call__(self, client: Client, message: Message) -> bool:
        """Check if the message contains one of the allowed commands.

        This method attempts to parse the message as a command and checks
        if it matches any of the allowed command patterns.

        Args:
            client: The client instance
            message: The message to check

        Returns:
            bool: True if the message matches any allowed command, False otherwise
        """
        if not (message.text or message.caption):
            return False

        try:
            await self.parse_command(client, message)
            return True
        except CommandError:
            return False

    def validate_prefix(self, command: CommandObject) -> None:
        """Validate that the command uses an allowed prefix.

        Args:
            command: The command object to validate

        Raises:
            CommandError: If the prefix is not among the allowed prefixes
        """
        prefix = command.prefix.lower() if self.ignore_case and command.prefix else command.prefix
        valid_prefixes = (
            [p.lower() for p in self.command_prefixes]
            if self.ignore_case
            else self.command_prefixes
        )
        if prefix not in valid_prefixes:
            msg = f"Invalid prefix: {command.prefix!r}."
            raise CommandError(msg)

    async def validate_mention(self, client: Client, command: CommandObject) -> None:
        """Validate the bot mention in the command (if present).

        Args:
            client: The client instance
            command: The command object to validate

        Raises:
            CommandError: If the mention doesn't match the bot's username
        """
        if command.mention and not self.ignore_mention:
            me = client.me or await client.get_me()
            if me.username and command.mention.lower() != me.username.lower():
                msg = f"Invalid mention: {command.mention!r}."
                raise CommandError(msg)

    def validate_command(self, command: CommandObject) -> CommandObject:
        """Validate that the command matches one of the allowed patterns.

        Args:
            command: The command object to validate

        Returns:
            CommandObject: The command object with regexp_match set if matched

        Raises:
            CommandError: If the command doesn't match any allowed pattern
        """
        cmd_name = command.command.lower() if self.ignore_case else command.command
        for allowed_cmd in self.command_patterns:
            match = allowed_cmd.match(cmd_name)
            if match:
                return replace(command, regexp_match=match)
        msg = f"Invalid command: {command.command!r}."
        raise CommandError(msg)

    async def parse_command(self, client: Client, message: Message) -> CommandObject:
        """Parse and validate a command from a message.

        This method performs complete processing of a command message:
        1. Parses the message text to extract command components
        2. Validates the command prefix
        3. Validates the bot mention (if present)
        4. Checks if the command is disabled in the current chat
        5. Validates that the command matches an allowed pattern
        6. Applies the magic filter (if provided)

        Args:
            client: The client instance
            message: The message containing the command

        Returns:
            CommandObject: The fully validated command object

        Raises:
            CommandError: If any validation step fails
        """
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
        """Apply the magic filter to the command if one is provided.

        Args:
            command: The command object to filter

        Returns:
            CommandObject: The command object with magic_result set if matched

        Raises:
            CommandError: If the magic filter rejects the command
        """
        if self.magic:
            result = self.magic.resolve(command)
            if result:
                return replace(command, magic_result=result)
            msg = "Rejected by magic filter."
            raise CommandError(msg)
        return command
