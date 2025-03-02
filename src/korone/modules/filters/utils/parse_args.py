# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram.types import Message


def parse_args(
    args: str, reply_message: Message | None = None
) -> tuple[tuple[str, ...], str] | None:
    # Match args in the format "(filter1, filter2, ...) content"
    if match := re.match(r"^\((.*?)\)\s*(.*)$", args, re.DOTALL):
        return _parse_multiple_filters(match, reply_message)

    # If there's a reply message and no args, return the stripped args
    if reply_message and not args.strip():
        return ((args.strip().strip('"'),), "")

    # Parse single filter
    return _parse_single_filter(args, reply_message)


def _parse_multiple_filters(
    match: re.Match, reply_message: Message | None = None
) -> tuple[tuple[str, ...], str]:
    filter_names, filter_content = match.groups()
    filter_content = "" if reply_message else filter_content.strip()

    # Regex explanation:
    # Split on commas, but not within quoted strings
    split_pattern = r"""
        ,\s*            # Comma followed by optional whitespace
        (?=             # Positive lookahead
            (?:         # Non-capturing group
                [^"]*   # Any number of non-quote characters
                "       # A quote
                [^"]*   # Any number of non-quote characters
                "       # Another quote
            )*          # Any number of quote pairs
            [^"]*       # Followed by any number of non-quote characters
            $           # Until the end of the string
        )
    """
    filters = tuple(
        filter_name.strip().strip('"')
        for filter_name in re.split(split_pattern, filter_names, flags=re.VERBOSE)
    )
    return filters, filter_content


def _parse_single_filter(
    args: str, reply_message: Message | None = None
) -> tuple[tuple[str, ...], str] | None:
    if reply_message:
        return ((args.strip().strip('"'),), "")

    args = args.strip()
    if args.startswith('"'):
        # Find the closing quote
        end_quote = args.find('"', 1)
        if end_quote != -1:
            filter_name = args[1:end_quote]
            filter_content = args[end_quote + 1 :].strip()
            return ((filter_name,), filter_content)
    else:
        # Split on the first whitespace
        parts = args.split(None, 1)
        if len(parts) == 2:
            return ((parts[0],), parts[1])

    return None
