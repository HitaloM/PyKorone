# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from contextlib import suppress
from typing import TYPE_CHECKING

from hydrogram.filters import Filter

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message

RegexPatternType = str | re.Pattern


class RegexError(Exception):
    pass


class Regex(Filter):
    __slots__ = ("ignore_case", "patterns")

    def __init__(
        self,
        *values: RegexPatternType,
        patterns: Sequence[RegexPatternType] | RegexPatternType | None = None,
        ignore_case: bool = False,
    ) -> None:
        patterns = self._prepare_patterns(values, patterns, ignore_case)
        if not patterns:
            msg = "Regex filter requires at least one pattern"
            raise ValueError(msg)

        self.patterns = tuple(patterns)
        self.ignore_case = ignore_case

    def _prepare_patterns(self, values, patterns, ignore_case):
        if isinstance(patterns, str | re.Pattern):
            patterns = [patterns]
        elif patterns is None:
            patterns = []

        if not isinstance(patterns, Iterable):
            msg = "Regex filter only supports str, re.Pattern object or their Iterable"
            raise TypeError(msg)

        return [self._process_pattern(pattern, ignore_case) for pattern in (*values, *patterns)]

    @staticmethod
    def _process_pattern(pattern, ignore_case):
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

        return any(pattern.search(text) for pattern in self.patterns)
