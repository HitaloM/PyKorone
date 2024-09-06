# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.lastfm.utils import (
    LastFMClient,
    LastFMError,
    TimePeriod,
    create_album_collage,
    get_lastfm_user_or_reply,
    handle_lastfm_error,
    name_with_link,
    parse_collage_arg,
    period_to_str,
)
from korone.utils.i18n import gettext as _


@router.message(Command("lfmcollage"))
async def lfmcollage_command(client: Client, message: Message) -> None:
    last_fm_user = await get_lastfm_user_or_reply(message)
    if not last_fm_user:
        return

    command = CommandObject(message).parse()
    collage_size = 3
    period = TimePeriod.AllTime
    show_text = True

    if args := command.args:
        collage_size, period, _entry_type, no_text = parse_collage_arg(args)
        show_text = not no_text

    last_fm = LastFMClient()

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
    ):
        try:
            top_items = await last_fm.get_top_albums(last_fm_user, period, limit=collage_size**2)
        except LastFMError as e:
            await handle_lastfm_error(message, e)
            return

        if not top_items:
            await message.reply(_("No top albums found for your LastFM account."))
            return

        collage_path = await create_album_collage(
            top_items, collage_size=(collage_size, collage_size), show_text=show_text
        )

        user_link = name_with_link(name=str(message.from_user.first_name), username=last_fm_user)
        caption = f"{user_link}\n{collage_size}x{collage_size}, albums, {period_to_str(period)}"

        await message.reply_photo(photo=collage_path, caption=caption)
