# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import regex as re

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
