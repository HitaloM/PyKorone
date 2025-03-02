# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html

from hydrogram.types import Message

from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils.errors import LastFMError
from korone.utils.i18n import gettext as _


async def get_lastfm_user_or_reply(message: Message) -> str | None:
    last_fm_user = await get_lastfm_user(message.from_user.id)
    if not last_fm_user:
        await message.reply(
            _(
                "You need to set your LastFM username first! "
                "Example: <code>/setlfm username</code>."
            )
        )
        return None
    return last_fm_user


async def handle_lastfm_error(message: Message, error: LastFMError) -> None:
    if "User not found" in error.message:
        await message.reply(_("Your LastFM username was not found! Try setting it again."))
    else:
        await message.reply(
            _(
                "An error occurred while fetching your LastFM data!"
                "\n<blockquote>{error}</blockquote>"
            ).format(error=error.message)
        )


def build_response_text(
    user_link: str,
    now_playing: bool,
    entity_name: str,
    entity_type: str,
    playcount: int,
    tags: str = "",
) -> str:
    text = (
        _("{user}'s is listening to:\n").format(user=user_link)
        if now_playing
        else _("{user}'s was listening to:\n").format(user=user_link)
    )
    text += f"{entity_type} <b>{html.escape(entity_name)}</b>"
    if playcount > 0:
        text += _(" ∙ <code>{playcount} plays</code>").format(playcount=playcount)
    if tags:
        text += f"\n\n{tags}"
    return text
