# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command
from korone.modules.lastfm.database import save_lastfm_user
from korone.utils.i18n import gettext as _


@router.message(Command("setlfm"))
async def setlfm_command(client: Client, message: Message) -> None:
    username = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None

    if not username:
        await message.reply(
            _("You need to provide your LastFM username! Example: <code>/setlfm username</code>.")
        )
        return

    if not re.match(r"^[A-Za-z0-9_]*$", username):
        await message.reply(_("LastFM username must not contain spaces or special characters!"))
        return

    await save_lastfm_user(user_id=message.from_user.id, username=username)
    await message.reply(_("LastFM username set successfully!"))
