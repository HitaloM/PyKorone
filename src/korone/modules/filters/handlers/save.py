# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsAdmin
from korone.modules.filters.database import save_filter, update_filters_cache
from korone.modules.filters.utils.parse_args import parse_args
from korone.modules.filters.utils.parse_filter import parse_saveable
from korone.utils.i18n import gettext as _


@router.message(Command("filter") & IsAdmin)
async def filter_command(client: Client, message: Message) -> None:
    command_obj = CommandObject(message).parse()

    if not command_obj.args:
        await message.reply(
            _(
                "You need to provide arguments to save a filter. "
                "Example: <code>/filter filtername</code>"
            )
        )
        return

    filters = parse_args(command_obj.args.lower(), message.reply_to_message)
    if not filters:
        await message.reply(
            _("Invalid filter format. Check <code>/help</code> for more information.")
        )
        return

    filter_names, filter_content = filters
    if not filter_content:
        await message.reply(
            _(
                "You need to provide the filter content. "
                "Check <code>/help</code> for more information."
            )
        )
        return

    filter_names, filter_content = filters
    save_data = await parse_saveable(message, filter_content or "", allow_reply_message=True)
    if not save_data or not save_data.text:
        await message.reply("Something went wrong while saving the filter.")
        return

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

    await update_filters_cache(message.chat.id)

    response_message = format_saved_filters_message(message, filter_names)
    await message.reply(response_message)


def format_saved_filters_message(message: Message, filter_names: tuple[str, ...]) -> str:
    saved_filters = list(filter_names)
    return _("Saved {count} filters in {chat}:\n{filters}").format(
        count=len(saved_filters),
        chat=message.chat.title or _("private chat"),
        filters="\n".join(f"- <code>{filter_name}</code>" for filter_name in saved_filters),
    )
