from __future__ import annotations

from html import escape
from io import BytesIO
from typing import TYPE_CHECKING

from aiogram.types import BufferedInputFile

from korone.config import CONFIG
from korone.db.repositories.lastfm import LastFMRepository
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.formatters import name_with_link
from korone.modules.lastfm.utils.lastfm_api import LastFMClient
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import Message

    from korone.modules.lastfm.utils.types import LastFMTrack


async def get_lastfm_user_or_reply(message: Message) -> str | None:
    if not CONFIG.lastfm_key:
        await message.reply(_("Last.fm API key is not configured. Please contact the bot owner."))
        return None

    if not message.from_user:
        await message.reply(_("Could not identify your user."))
        return None

    last_fm_user = await LastFMRepository.get_username(message.from_user.id)
    if not last_fm_user:
        await message.reply(_("You need to set your Last.fm username first! Example: <code>/setlfm username</code>."))
        return None

    return last_fm_user


async def handle_lastfm_error(message: Message, error: LastFMError) -> None:
    if "User not found" in error.message:
        await message.reply(_("Your Last.fm username was not found! Try setting it again."))
    elif "API key" in error.message:
        await message.reply(_("Last.fm API key is not configured. Please contact the bot owner."))
    else:
        raise error


def get_user_link(message: Message, lastfm_username: str) -> str:
    name = str(message.from_user.first_name) if message.from_user else lastfm_username
    return name_with_link(name=name, username=lastfm_username)


async def fetch_and_handle_recent_track(message: Message, lastfm_username: str) -> tuple[LastFMTrack, str] | None:
    last_fm = LastFMClient()
    try:
        recent_tracks = await last_fm.get_recent_tracks(lastfm_username, limit=1)
        if not recent_tracks:
            await message.reply(_("No recent tracks found for your Last.fm account."))
            return None
        last_played = recent_tracks[0]
    except LastFMError as exc:
        await handle_lastfm_error(message, exc)
        return None

    return last_played, get_user_link(message, lastfm_username)


def build_entity_response(
    *, user_link: str, now_playing: bool, emoji: str, entity_name: str, playcount: int = 0, tags: str = ""
) -> str:
    if now_playing:
        text = _("{user}'s is listening to:\n").format(user=user_link)
    else:
        text = _("{user}'s was listening to:\n").format(user=user_link)

    text += f"{emoji} <b>{escape(entity_name)}</b>"

    if playcount > 0:
        text += _(" ∙ <code>{playcount} plays</code>").format(playcount=playcount)

    if tags:
        text += f"\n\n{tags}"

    return text


async def reply_with_optional_image(
    message: Message, text: str, photo: BytesIO | str | None = None, *, filename: str = "lastfm.jpg"
) -> None:
    if photo:
        if isinstance(photo, BytesIO):
            file = BufferedInputFile(photo.getvalue(), filename=getattr(photo, "name", filename))
            await message.reply_photo(photo=file, caption=text)
            return

        await message.reply_photo(photo=photo, caption=text)
        return

    await message.reply(text, disable_web_page_preview=True)
