# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.translator.utils import DeepL, QuotaExceededError, TranslationError
from korone.utils.i18n import gettext as _

# fmt: off
SUPPORTED_SOURCE_LANGUAGES: set[str] = {
    "BG", "CS", "DA", "DE", "EL", "EN", "ES", "ET", "FI", "FR", "HU",
    "ID", "IT", "JA", "KO", "LT", "LV", "NB", "NL", "PL", "PT", "RO",
    "RU", "SK", "SL", "SV", "TR", "UK", "ZH"
}

SUPPORTED_TARGET_LANGUAGES: set[str] = {
    "BG", "CS", "DA", "DE", "EL", "EN", "EN-GB", "EN-US", "ES", "ET",
    "FI", "FR", "HU", "ID", "IT", "JA", "KO", "LT", "LV", "NB", "NL",
    "PL", "PT", "PT-BR", "PT-PT", "RO", "RU", "SK", "SL", "SV", "TR",
    "UK", "ZH"
}
# fmt: on


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
        elif len(parts) == 1 and ":" not in parts[0]:
            target_lang = parts[0]
            text = get_reply_text(message)
        elif len(parts) == 2:
            target_lang, text = parts
        else:
            text = command.args
    elif message.reply_to_message:
        text = get_reply_text(message)

    return source_lang, target_lang, text


@router.message(Command(commands=["tr", "translate"]))
async def translate_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()
    source_lang, target_lang, text = extract_translation_details(message, command)

    source_lang = source_lang.upper() if source_lang else None
    target_lang = target_lang.upper()

    if source_lang and source_lang not in SUPPORTED_SOURCE_LANGUAGES:
        await message.reply(
            _("Unsupported source language: {source_lang}").format(source_lang=source_lang)
        )
        return

    if target_lang not in SUPPORTED_TARGET_LANGUAGES:
        await message.reply(
            _("Unsupported target language: {target_lang}").format(target_lang=target_lang)
        )
        return

    if not text:
        await message.reply(_("The text to translate is empty. Please provide some text."))
        return

    try:
        deepl = DeepL()
        translation = await deepl.translate_text(text, target_lang, source_lang)
    except QuotaExceededError:
        await message.reply(
            _(
                "Korone has reached the translation quota. The DeepL API has a limit of "
                "500,000 characters per month for the free plan, and we have exceeded "
                "this limit."
            )
        )
        return
    except TranslationError as e:
        await message.reply(_("Failed to translate text. Error: {error}").format(error=e))
        return

    response_text = _(
        "<b>Language:</b> <code>{source_lang}</code> => <code>{target_lang}</code>"
    ).format(source_lang=translation.detected_source_language, target_lang=target_lang.upper())
    response_text += f"\n<b>Translation:</b> <code>{translation.text}</code>"
    await message.reply(response_text)
