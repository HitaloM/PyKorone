# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from re import Pattern
from typing import TYPE_CHECKING, Final

from hydrogram.filters import Filter

from korone.modules.core import COMMANDS

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message

RegexPatternType = str | Pattern[str]


class RegexError(Exception):
    """Exception raised when there's an error with regex patterns in filters."""

    pass


class Regex(Filter):
    """Filter for matching messages against regex patterns.

    This filter checks if a message's text or caption matches any of the provided
    regex patterns. It supports both string patterns that will be compiled to regex,
    and pre-compiled regex Pattern objects.

    Attributes:
        patterns: Compiled regex patterns to match against
        ignore_case: Whether to ignore case when matching
        friendly_name: Optional name for identifying the regex filter in logs and for disabling
    """

    __slots__ = ("friendly_name", "ignore_case", "patterns")

    def __init__(
        self,
        *values: RegexPatternType,
        patterns: Sequence[RegexPatternType] | RegexPatternType | None = None,
        ignore_case: bool = False,
        friendly_name: str | None = None,
    ) -> None:
        """Initialize the regex filter.

        Args:
            *values: Variable length regex patterns
            patterns: Additional regex patterns as a sequence or single pattern
            ignore_case: Whether to ignore case when matching
            friendly_name: Name for the regex filter (used for disabling)

        Raises:
            ValueError: If no patterns are provided
            TypeError: If patterns are not of the supported types
            RegexError: If a pattern string cannot be compiled to a valid regex
        """
        try:
            prepared_patterns = self._prepare_patterns(values, patterns, ignore_case)
        except (TypeError, RegexError):
            raise
        if not prepared_patterns:
            msg = "Regex filter requires at least one pattern."
            raise ValueError(msg)

        self.patterns: Final[tuple[Pattern[str], ...]] = tuple(prepared_patterns)
        self.ignore_case = ignore_case
        self.friendly_name = friendly_name

    def _prepare_patterns(
        self,
        values: Iterable[RegexPatternType],
        patterns: Sequence[RegexPatternType] | RegexPatternType | None,
        ignore_case: bool,
    ) -> list[Pattern[str]]:
        """Prepare and compile regex patterns.

        Args:
            values: Patterns passed as positional arguments
            patterns: Patterns passed via the patterns parameter
            ignore_case: Whether to ignore case when compiling patterns

        Returns:
            list[Pattern[str]]: List of compiled regex patterns

        Raises:
            TypeError: If patterns are not of supported types
        """
        if isinstance(patterns, (str, Pattern)):
            patterns = [patterns]
        elif patterns is None:
            patterns = []
        elif not isinstance(patterns, Iterable):
            msg = "Regex filter only supports str, re.Pattern objects or their Iterable."
            raise TypeError(msg)

        combined_patterns = list(values) + list(patterns)
        return [self._process_pattern(p, ignore_case) for p in combined_patterns]

    @staticmethod
    def _process_pattern(pattern: RegexPatternType, ignore_case: bool) -> Pattern[str]:
        """Process and compile a single pattern.

        Args:
            pattern: The regex pattern as string or Pattern object
            ignore_case: Whether to ignore case when compiling

        Returns:
            Pattern[str]: Compiled regex pattern

        Raises:
            RegexError: If the pattern string cannot be compiled
            TypeError: If the pattern is not of a supported type
        """
        if isinstance(pattern, str):
            flags = re.IGNORECASE if ignore_case else 0
            try:
                return re.compile(pattern, flags)
            except re.error as e:
                msg = f"Invalid regex pattern: {pattern}. Please check the pattern syntax."
                raise RegexError(msg) from e
        if not isinstance(pattern, Pattern):
            msg = "Regex filter only supports str or re.Pattern objects."
            raise TypeError(msg)
        return pattern

    async def __call__(self, client: Client, message: Message) -> bool:
        """Check if the message matches any of the regex patterns.

        Args:
            client: The client instance
            message: The message to check

        Returns:
            bool: True if the message matches any pattern, False otherwise
        """
        if not (message.text or message.caption):
            return False

        with suppress(RegexError):
            return await self.parse_regex(message)
        return False

    async def parse_regex(self, message: Message) -> bool:
        """Parse message text against regex patterns.

        Args:
            message: The message to check

        Returns:
            bool: True if the message matches any pattern

        Raises:
            RegexError: If the regex is disabled in the current chat
        """
        text = message.text or message.caption
        if not text:
            return False

        if self.friendly_name and self.friendly_name in COMMANDS:
            chat_id = message.chat.id
            if not COMMANDS[self.friendly_name]["chat"].get(chat_id, True):
                msg = f"Regex pattern '{self.friendly_name}' is disabled in chat '{chat_id}'"
                raise RegexError(msg)

        return any(pattern.search(text) for pattern in self.patterns)
