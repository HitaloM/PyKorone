# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
from contextlib import suppress
from typing import Any, cast

from hydrogram.types import Message, User

from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils.deezer_api import DeezerClient, DeezerError
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.formatters import format_tags, name_with_link
from korone.modules.lastfm.utils.image_filter import get_biggest_lastfm_image
from korone.modules.lastfm.utils.lastfm_api import LastFMClient
from korone.modules.lastfm.utils.types import LastFMAlbum, LastFMArtist, LastFMTrack
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


async def fetch_and_handle_recent_track(
    message: Message, lastfm_username: str
) -> tuple[LastFMTrack, str] | None:
    last_fm = LastFMClient()
    try:
        recent_tracks = await last_fm.get_recent_tracks(lastfm_username, limit=1)
        if not recent_tracks:
            await message.reply(_("No recent tracks found for your LastFM account."))
            return None
        last_played = recent_tracks[0]
    except LastFMError as e:
        await handle_lastfm_error(message, e)
        return None
    except IndexError:
        await message.reply(_("No recent tracks found for your LastFM account."))
        return None

    user_link = name_with_link(name=str(message.from_user.first_name), username=lastfm_username)
    return last_played, user_link


async def get_entity_info(
    last_fm: LastFMClient,
    last_played: LastFMTrack,
    lastfm_username: str,
    info_type: str,
) -> LastFMArtist | LastFMAlbum | LastFMTrack | None:
    with suppress(LastFMError):
        if info_type == "artist":
            return await last_fm.get_artist_info(last_played.artist.name, lastfm_username)
        if info_type == "album" and last_played.album:
            return await last_fm.get_album_info(
                last_played.artist.name,
                cast("str", last_played.album.name),
                lastfm_username,
            )
        if info_type == "track":
            return await last_fm.get_track_info(
                last_played.artist.name, last_played.name, lastfm_username
            )
    return None


async def send_entity_response(
    message: Message,
    last_played: LastFMTrack,
    user_link: str,
    entity_info: Any,
    entity_type: str,
    entity_name: str,
    get_image: bool = True,
) -> None:
    text = build_response_text(
        user_link=user_link,
        now_playing=last_played.now_playing,
        entity_name=entity_name,
        entity_type=entity_type,
        playcount=getattr(entity_info, "playcount", 0) if entity_info else 0,
        tags=format_tags(entity_info)
        if entity_info and hasattr(entity_info, "tags") and entity_info.tags
        else "",
    )

    if get_image:
        if entity_type == "👨‍🎤":
            with suppress(DeezerError):
                deezer = DeezerClient()
                artist = await deezer.get_artist(last_played.artist.name)
                if artist and (picture := artist.picture_xl or artist.picture_big):
                    await message.reply_photo(photo=picture, caption=text)
                    return

        image = await get_biggest_lastfm_image(last_played)
        if image:
            await message.reply_photo(photo=image, caption=text)
            return

    await message.reply(text, disable_web_page_preview=True)


async def check_compatibility_users(message: Message, user1: User, user2: User) -> bool:
    if user1.id == user2.id:
        await message.reply(_("You can't get the compatibility with yourself!"))
        return False

    if user1.is_bot or user2.is_bot:
        await message.reply(_("Bots won't have music taste!"))
        return False

    return True


async def fetch_lastfm_users(
    message: Message, user1_id: int, user2_id: int
) -> tuple[str | None, str | None]:
    user1_db = await get_lastfm_user(user1_id)
    user2_db = await get_lastfm_user(user2_id)

    if not user1_db:
        await message.reply(
            _(
                "You need to set your LastFM username first! "
                "Example: <code>/setlfm username</code>."
            )
        )

    if not user2_db:
        await message.reply(
            _(
                "The user you replied to doesn't have a LastFM account linked! "
                "Hint them to set it using <code>/setlfm username</code>."
            )
        )

    return user1_db, user2_db
