# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import functools
import re

from anyio import fail_after
from cashews import suppress
from hydrogram import Client, filters
from hydrogram.enums import ParseMode
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import HasText, UserIsAdmin
from korone.filters.command import CommandError, CommandObject
from korone.modules.filters.database import get_filters_cache, update_filters_cache
from korone.modules.filters.utils.buttons import unparse_buttons, unparse_buttons_to_text
from korone.modules.filters.utils.text import vars_parser
from korone.modules.filters.utils.types import FilterModel
from korone.utils.concurrency import run_blocking


@router.message(HasText() & ~filters.bot)
async def check_filters(client: Client, message: Message) -> None:
    chat_id = message.chat.id

    chat_filters = await get_filters_cache(chat_id) or await update_filters_cache(chat_id)
    if not chat_filters:
        return

    text = message.text or message.caption

    command_obj = None
    with suppress(CommandError):
        command_obj = CommandObject(message).parse()

    if (
        command_obj
        and await UserIsAdmin(client, message, show_alert=False)
        and command_obj.command.startswith((
            "filter",
            "delfilter",
            "filterinfo",
        ))
    ):
        return

    compiled_patterns = [
        (filter, re.compile(rf"( |^|[^\w]){re.escape(name)}( |$|[^\w])", re.IGNORECASE))
        for filter in chat_filters
        for name in filter.names
    ]

    for filter, pattern in compiled_patterns:
        try:
            with fail_after(0.2):
                matched = await run_blocking(functools.partial(re.search, pattern, text))
            if matched:
                await send_filter(message, filter, noformat="noformat" in text)
                return
        except TimeoutError:
            continue


async def send_filter(message: Message, filter: FilterModel, noformat: bool = False) -> None:
    buttons = None if noformat else unparse_buttons(filter.buttons) if filter.buttons else None
    parsed_text = (
        filter.text
        if noformat
        else vars_parser(filter.text, message, message.from_user)
        if filter.text
        else None
    )

    if noformat and filter.buttons:
        text_buttons = unparse_buttons_to_text(filter.buttons)
        parsed_text = f"{parsed_text}\n{text_buttons}" if parsed_text else text_buttons

    if filter.content_type == "text" and parsed_text:
        await message.reply(
            parsed_text,
            reply_markup=buttons,
            disable_web_page_preview=True,
            parse_mode=ParseMode.DISABLED if noformat else ParseMode.HTML,
        )
        return

    if not filter.file:
        return

    content_type_methods = {
        "photo": message.reply_photo,
        "video": message.reply_video,
        "audio": message.reply_audio,
        "voice": message.reply_voice,
        "document": message.reply_document,
        "sticker": message.reply_sticker,
        "animation": message.reply_animation,
    }

    reply_method = content_type_methods.get(filter.content_type)
    if not reply_method:
        return

    if filter.content_type == "sticker":
        await reply_method(filter.file.file_id)
        return

    await reply_method(
        filter.file.file_id,
        caption=parsed_text or "",
        reply_markup=buttons,
        parse_mode=ParseMode.DISABLED if noformat else ParseMode.HTML,
    )
