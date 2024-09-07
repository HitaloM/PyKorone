# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters.command import Command
from korone.modules.piston.utils.api import get_languages
from korone.utils.i18n import gettext as _


@router.message(Command("pistonlangs"))
async def langs_handler(client: Client, message: Message) -> None:
    languages = await get_languages()
    if not languages:
        await message.reply(_("Failed to fetch the available languages."))
        return

    text = _("<b>Supported languages</b>:\n")
    text += "\n".join(f"- <code>{lang}</code>" for lang in languages)
    await message.reply(text)
