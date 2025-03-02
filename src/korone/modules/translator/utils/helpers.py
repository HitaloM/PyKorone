# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import Message

from korone.filters import CommandObject


def get_reply_text(message: Message) -> str:
    if message.reply_to_message:
        return message.reply_to_message.text or message.reply_to_message.caption or ""
    return ""


def extract_translation_details(
    message: Message, command: CommandObject
) -> tuple[str | None, str, str]:
    default_lang = "EN"
    source_lang = None
    target_lang = default_lang
    text = ""

    if command.args:
        parts = command.args.split(" ", 1)
        if parts[0].count(":") == 1:
            source_lang, target_lang = parts[0].split(":", 1)
            text = parts[1] if len(parts) > 1 else get_reply_text(message)
        else:
            text = command.args
    elif message.reply_to_message:
        text = get_reply_text(message)

    return source_lang, target_lang, text
