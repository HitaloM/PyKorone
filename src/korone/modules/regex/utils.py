from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aiogram.filters import BaseFilter

if TYPE_CHECKING:
    from aiogram.types import Message

from korone.utils.i18n import gettext as _

SED_PATTERN: re.Pattern[str] = re.compile(r"^s/((?:\\.|[^/])+)/((?:\\.|[^/])*)(/.*)?")
GROUP0_RE: re.Pattern[str] = re.compile(r"(?<!\\)((?:\\\\)*)\\0")
MAX_PATTERN_LENGTH = 1000


class SedPatternFilter(BaseFilter):
    def __init__(self, pattern: re.Pattern[str]) -> None:
        self.pattern = pattern

    async def __call__(self, message: Message) -> bool:
        text = message.text or ""
        return bool(text and self.pattern.match(text))


def cleanup_pattern(match: re.Match[str]) -> tuple[str, str]:
    from_pattern = match.group(1)
    to_pattern = match.group(2).replace("\\/", "/")
    to_pattern = GROUP0_RE.sub(r"\1\\g<0>", to_pattern)
    return from_pattern, to_pattern


def build_flags_and_count(flags_str: str) -> tuple[int, int]:
    flags = 0
    count = 1
    for flag in flags_str:
        match flag:
            case "i":
                flags |= re.IGNORECASE
            case "m":
                flags |= re.MULTILINE
            case "s":
                flags |= re.DOTALL
            case "g":
                count = 0
            case "x":
                flags |= re.VERBOSE
            case _:
                msg = f"Unknown flag: {flag}"
                raise ValueError(msg, flag)
    return flags, count


def process_command(command: str) -> tuple[None, str] | tuple[tuple[str, str, int, int], None]:
    if not (command_match := re.match(SED_PATTERN, command)):
        return None, _("Invalid command: {command}").format(command=command)

    from_pattern, to_pattern = cleanup_pattern(command_match)
    flags_str = (command_match.group(3) or "")[1:]

    if len(from_pattern) > MAX_PATTERN_LENGTH or len(to_pattern) > MAX_PATTERN_LENGTH:
        return None, _("Pattern is too long. Please use shorter patterns.")

    try:
        flags, count = build_flags_and_count(flags_str)
    except ValueError as e:
        return None, _("Unknown flag: {flag}").format(flag=e.args[1])

    return (from_pattern, to_pattern, flags, count), None
