# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
import re
from contextlib import suppress

from anyio import sleep
from hydrogram import Client, filters
from hydrogram.enums import MessageEntityType
from hydrogram.errors import BadRequest, MessageDeleteForbidden, PeerIdInvalid
from hydrogram.types import Message, MessageEntity, User

from korone.decorators import router
from korone.modules.afk.database import get_afk_reason, get_user, is_afk, set_afk
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils.errors import LastFMError
from korone.modules.lastfm.utils.lastfm_api import LastFMClient
from korone.utils.i18n import gettext as _


@router.message(~filters.private & ~filters.bot)
async def afk_checker(client: Client, message: Message) -> None:
    if message.from_user and message.text and re.findall(r"^\/\bafk\b", message.text):
        return

    if await is_afk(message.from_user.id):
        await set_afk(message.from_user.id, state=False)
        sent = await message.reply(_("Oh, you're back! I've removed your afk status."))
        await sleep(5)
        with suppress(BadRequest, MessageDeleteForbidden):
            await sent.delete()
    else:
        if message.entities:
            for entity in message.entities:
                user = await get_user_from_entity(entity, client, message)
                if user:
                    await send_afk_message(user, message)
        if message.reply_to_message and message.reply_to_message.from_user:
            await send_afk_message(message.reply_to_message.from_user, message)


async def get_user_from_entity(
    entity: MessageEntity, client: Client, message: Message
) -> User | None:
    if entity.type == MessageEntityType.MENTION:
        username = message.text[entity.offset : entity.offset + entity.length]
        normalized_username = username.lstrip("@")

        try:
            return await client.get_chat(username)  # pyright: ignore[reportReturnType]
        except (PeerIdInvalid, BadRequest, KeyError):
            with suppress(PeerIdInvalid, BadRequest, KeyError):
                user = await client.get_users(normalized_username)
                if isinstance(user, list):
                    user = next((item for item in user if isinstance(item, User)), None)
                if isinstance(user, User):
                    return user

            data = await get_user(username)
            if not data:
                return None

            chat_id = data[0]["id"]
            try:
                return await client.get_chat(chat_id)  # pyright: ignore[reportReturnType]
            except PeerIdInvalid:
                return None
    elif entity.type == MessageEntityType.TEXT_MENTION:
        return entity.user

    return None


async def send_afk_message(user: User, message: Message) -> None:
    if not user or user.id == message.from_user.id or not await is_afk(user.id):
        return

    text = _("{user} is afk!").format(user=user.first_name)
    reason = await get_afk_reason(user.id)
    if reason:
        text += _("\nReason: {reason}").format(reason=html.escape(reason))

    lastfm_text = await get_lastfm_status(user.id)
    if lastfm_text:
        text += lastfm_text

    sent = await message.reply(text)
    await sleep(5)
    with suppress(BadRequest, MessageDeleteForbidden):
        await sent.delete()


async def get_lastfm_status(user_id: int) -> str | None:
    last_fm_user = await get_lastfm_user(user_id)
    if not last_fm_user:
        return None

    last_fm = LastFMClient()
    try:
        last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
        if last_played.now_playing:
            track_info = await last_fm.get_track_info(
                last_played.artist.name, last_played.name, last_fm_user
            )
            return _("\n🎧 Listening to: {track_artist} — {track_name}").format(
                track_artist=html.escape(track_info.artist.name),
                track_name=html.escape(track_info.name),
            )
    except (LastFMError, IndexError):
        return None

    return None
