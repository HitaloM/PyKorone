# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram.types import Message


def parse_args(args: str, reply_message: Message | None = None) -> dict[str, str] | None:
    if match := re.match(r"^\((.*?)\)\s*(.*)$", args):
        return _parse_multiple_filters(match, reply_message)

    if reply_message and not args.strip():
        return {args.strip().strip('"'): ""}

    return _parse_single_filter(args, reply_message)


def _parse_multiple_filters(
    match: re.Match, reply_message: Message | None = None
) -> dict[str, str]:
    filter_names, filter_content = match.groups()

    if reply_message and not filter_content.strip():
        filter_content = ""

    return {
        filter_name.strip().strip('"'): filter_content
        for filter_name in re.split(r',\s*(?=(?:[^"]*"[^"]*")*[^"]*$)', filter_names)
    }


def _parse_single_filter(args: str, reply_message: Message | None = None) -> dict[str, str]:
    if reply_message:
        return {args.strip().strip('"'): ""}

    if match := re.match(r'^"([^"]+)"\s+(.*)$|^(\S+)\s+(.*)$', args):
        filter_name, filter_content = match[1] or match[3], match[2] or match[4]
        return {filter_name.strip().strip('"'): filter_content}

    return {}
