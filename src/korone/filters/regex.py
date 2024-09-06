# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from typing import TYPE_CHECKING, Any, cast

from hydrogram.filters import Filter

from korone.modules import COMMANDS

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message

RegexPatternType = str | re.Pattern


class RegexError(Exception):
    pass


class Regex(Filter):
    __slots__ = ("friendly_name", "ignore_case", "patterns")

    def __init__(
        self,
        *values: RegexPatternType,
        patterns: Sequence[RegexPatternType] | RegexPatternType | None = None,
        ignore_case: bool = False,
        friendly_name: str | None = None,
    ) -> None:
        patterns = self._prepare_patterns(values, patterns, ignore_case)
        if not patterns:
            msg = "Regex filter requires at least one pattern"
            raise ValueError(msg)

        self.patterns = tuple(patterns)
        self.ignore_case = ignore_case
        self.friendly_name = friendly_name

    def _prepare_patterns(
        self,
        values: Sequence[RegexPatternType],
        patterns: Sequence[RegexPatternType] | RegexPatternType | None,
        ignore_case: bool,
    ) -> list[re.Pattern]:
        if isinstance(patterns, str | re.Pattern):
            patterns = [patterns]
        elif patterns is None:
            patterns = []

        if not isinstance(patterns, Iterable):
            msg = "Regex filter only supports str, re.Pattern object or their Iterable"
            raise TypeError(msg)

        return [self._process_pattern(pattern, ignore_case) for pattern in (*values, *patterns)]

    @staticmethod
    def _process_pattern(pattern: RegexPatternType, ignore_case: bool) -> re.Pattern:
        if isinstance(pattern, str):
            flags = re.IGNORECASE if ignore_case else 0
            pattern = re.compile(pattern, flags)

        if not isinstance(pattern, re.Pattern):
            msg = "Regex filter only supports str, re.Pattern object or their Iterable"
            raise TypeError(msg)

        return pattern

    async def __call__(self, client: Client, message: Message) -> bool:
        if not (message.text or message.caption):
            return False

        with suppress(RegexError):
            return await self.parse_regex(message)

        return False

    async def parse_regex(self, message: Message) -> bool:
        text = message.text or message.caption
        if not text:
            return False

        if self.friendly_name and self.friendly_name in COMMANDS:
            chat_id = message.chat.id

            command_info = COMMANDS[self.friendly_name]
            if not isinstance(command_info, dict):
                msg = f"Invalid command info for {self.friendly_name}"
                raise RegexError(msg)

            command_info = cast(dict[str, Any], command_info)

            if not command_info["chat"].get(chat_id, True):
                msg = f"Regex pattern {self.friendly_name} is disabled in '{chat_id}'"
                raise RegexError(msg)

        return any(pattern.search(text) for pattern in self.patterns)
