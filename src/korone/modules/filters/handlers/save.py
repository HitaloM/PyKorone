# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsAdmin
from korone.modules.filters.database import save_filter, update_filters_cache
from korone.modules.filters.utils import parse_args, parse_saveable
from korone.utils.i18n import gettext as _


@router.message(Command("filter") & IsAdmin)
async def filter_command(client: Client, message: Message) -> None:
    command_obj = CommandObject(message).parse()

    if not command_obj.args:
        await message.reply(
            _(
                "You need to provide a name for the filter. "
                "Example: <code>/filter filtername</code>"
            )
        )
        return

    filters = parse_args(command_obj.args.lower(), message.reply_to_message)
    if not filters:
        await message.reply(
            _(
                "You need to provide the filter content. "
                "Check <code>/help</code> for more information."
            )
        )
        return

    await process_and_save_filters(message, filters)


async def process_and_save_filters(message: Message, filters: tuple[tuple[str, ...], str]) -> None:
    filter_names, filter_content = filters
    result = await save_single_filter(message, filter_names, filter_content)
    await update_filters_cache(message.chat.id)
    await reply_filter_status(message, [result])


async def save_single_filter(
    message: Message, filter_names: tuple[str, ...], filter_content: str
) -> tuple[str, ...]:
    save_data = await parse_saveable(message, filter_content or "", allow_reply_message=True)
    if not save_data:
        await message.reply("Something went wrong while saving the filter.")
        return filter_names

    await save_filter(
        chat_id=message.chat.id,
        filter_names=filter_names,
        filter_text=save_data.text,
        content_type=save_data.file.file_type if save_data.file else "text",
        creator_id=message.from_user.id,
        editor_id=message.from_user.id,
        file_id=save_data.file.file_id if save_data.file else "",
        buttons=save_data.buttons,
    )
    return filter_names


async def reply_filter_status(message: Message, results: list[tuple[str, ...]]) -> None:
    saved_filters = [name for names in results for name in names]

    if not saved_filters:
        return

    response_message = _("Saved {count} filters in {chat}:\n{filters}").format(
        count=len(saved_filters),
        chat=message.chat.title or _("private chat"),
        filters="\n".join(f"- <code>{filter_name}</code>" for filter_name in saved_filters),
    )

    await message.reply(response_message)
