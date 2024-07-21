# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import regex as re

from korone.utils.i18n import gettext as _

SED_PATTERN: str = r"^s/((?:\\.|[^/])+)/((?:\\.|[^/])*)(/.*)?"
GROUP0_RE: re.Pattern[str] = re.compile(r"(?<!\\)((?:\\\\)*)\\0")
MAX_PATTERN_LENGTH: int = 1000


def cleanup_pattern(match: re.Match) -> tuple[str, str]:
    from_pattern = match.group(1)
    to_pattern = match.group(2).replace("\\/", "/")
    to_pattern = GROUP0_RE.sub(r"\1\\g<0>", to_pattern)
    return from_pattern, to_pattern


def build_flags_and_count(flags_str: str) -> tuple[int, int]:
    flags = 0
    count = 1
    for flag in flags_str:
        if flag == "i":
            flags |= re.IGNORECASE
        elif flag == "m":
            flags |= re.MULTILINE
        elif flag == "s":
            flags |= re.DOTALL
        elif flag == "g":
            count = 0
        elif flag == "x":
            flags |= re.VERBOSE
        else:
            msg = f"Unknown flag: {flag}"
            raise ValueError(msg, flag)
    return flags, count


def process_command(command: str) -> tuple:
    command_match = re.match(SED_PATTERN, command)
    if not command_match:
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
