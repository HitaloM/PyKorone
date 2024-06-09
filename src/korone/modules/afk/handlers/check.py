# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import html
import re
from contextlib import suppress

from hydrogram import Client, filters
from hydrogram.enums import MessageEntityType
from hydrogram.errors import BadRequest, MessageDeleteForbidden, PeerIdInvalid
from hydrogram.types import Message, MessageEntity, User

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.modules.afk.database import get_afk_reason, get_user, is_afk, set_afk
from korone.modules.lastfm.database import get_lastfm_user
from korone.modules.lastfm.utils import LastFMClient, LastFMError
from korone.utils.i18n import gettext as _


class CheckAfk(MessageHandler):
    @staticmethod
    async def get_user(entity: MessageEntity, client: Client, message: Message) -> User | None:
        offset: int = entity.offset
        length: int = entity.length
        username: str = message.text[offset : offset + length]
        data = await get_user(username)

        if not data:
            return None

        chat_id = data[0]["id"]

        try:
            user: User = await client.get_chat(chat_id)  # type: ignore
        except PeerIdInvalid:
            return None

        return user

    async def handle_mentioned_users(self, client: Client, message: Message) -> None:
        if not message.entities:
            return

        for entity in message.entities:
            user: User | None = None
            if entity.type == MessageEntityType.MENTION:
                user = await self.get_user(entity, client, message)
            elif entity.type == MessageEntityType.TEXT_MENTION:
                user = entity.user

        if user is not None:
            await self.send_afk_message(user, message)

    async def handle_reply_to_message(self, message: Message) -> None:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return

        reply_user = message.reply_to_message.from_user
        await self.send_afk_message(reply_user, message)

    @staticmethod
    async def send_afk_message(user: User, message: Message) -> None:
        if not user or user.id == message.from_user.id or not await is_afk(user.id):
            return

        last_fm_user = await get_lastfm_user(user.id)
        reason = await get_afk_reason(user.id)
        track_text = None

        if last_fm_user:
            last_fm = LastFMClient()
            with suppress(LastFMError):
                last_played = (await last_fm.get_recent_tracks(last_fm_user, limit=1))[0]
                track_info = await last_fm.get_track_info(
                    last_played.artist, last_played.name, last_fm_user
                )
                track_text = _("🎧 Listening to: {track_artist} — {track_name}").format(
                    track_artist=track_info.artist, track_name=track_info.name
                )

        text = _("{user} is afk!").format(user=user.first_name)
        if reason:
            text += _("\nReason: {reason}").format(reason=html.escape(str(reason)))
        if track_text:
            text += f"\n{track_text}"

        await message.reply(text)

    @router.message(~filters.private & ~filters.bot, group=-2)
    async def handle(self, client: Client, message: Message) -> None:
        if message.from_user and message.text and re.findall(r"^\/\bafk\b", message.text):
            return

        if await is_afk(message.from_user.id):
            await set_afk(message.from_user.id, state=False)
            sent = await message.reply(_("Oh, you're back! I've removed your afk status."))
            await asyncio.sleep(5)
            with suppress(BadRequest, MessageDeleteForbidden):
                await sent.delete()
            return

        await self.handle_mentioned_users(client, message)
        await self.handle_reply_to_message(message)
