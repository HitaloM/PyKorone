# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram.types import Message


def parse_args(
    args: str, reply_message: Message | None = None
) -> tuple[tuple[str, ...], str] | None:
    if match := re.match(r"^\((.*?)\)\s*(.*)$", args, re.DOTALL):
        return _parse_multiple_filters(match, reply_message)

    if reply_message and not args.strip():
        return ((args.strip().strip('"'),), "")

    return _parse_single_filter(args, reply_message)


def _parse_multiple_filters(
    match: re.Match, reply_message: Message | None = None
) -> tuple[tuple[str, ...], str]:
    filter_names, filter_content = match.groups()
    filter_content = "" if reply_message else filter_content.strip()

    filters = tuple(
        filter_name.strip().strip('"')
        for filter_name in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', filter_names)
    )
    return filters, filter_content


def _parse_single_filter(
    args: str, reply_message: Message | None = None
) -> tuple[tuple[str, ...], str] | None:
    if reply_message:
        return ((args.strip().strip('"'),), "")

    if match := re.match(r'^"([^"]+)"\s+(.*)$|^(\S+)\s+(.*)$', args, re.DOTALL):
        filter_name = match[1] or match[3]
        filter_content = match[2] or match[4]
        return ((filter_name.strip().strip('"'),), filter_content)

    return None
