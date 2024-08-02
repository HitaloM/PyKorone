from aiogram import F, Router
from aiogram.types import Message

from sophie_bot.modules.legacy_modules.utils.connections import chat_connection
from sophie_bot.modules.legacy_modules.utils.disable import disableable_dec
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.modules.legacy_modules.utils.user_details import (
    get_admins_rights,
    get_user_link,
    is_user_admin,
)
from sophie_bot.services.db import db
from sophie_bot.utils.i18n import lazy_gettext as l_

router = Router(name="reports")

__module_name__ = l_("Reports")
__module_emoji__ = "🗳"


@register(router, F.text.regexp(r"^@admin(s)$"))
@chat_connection(only_groups=True)
@get_strings_dec("reports")
async def report1_cmd(message: Message, chat, strings):
    # Checking whether report is disabled in chat!
    check = await db.disabled.find_one({"chat_id": chat["chat_id"]})
    if check:
        if "report" in check["cmds"]:
            return
    await report(message, chat, strings)


@register(router, cmds="report")
@chat_connection(only_groups=True)
@disableable_dec("report")
@get_strings_dec("reports")
async def report2_cmd(message: Message, chat, strings):
    await report(message, chat, strings)


async def report(message: Message, chat, strings):
    user = message.from_user.id

    if (await is_user_admin(chat["chat_id"], user)) is True:
        return await message.reply(strings["user_user_admin"])

    if not message.reply_to_message:
        return await message.reply(strings["no_user_to_report"])

    offender_id = message.reply_to_message.from_user.id
    if (await is_user_admin(chat["chat_id"], offender_id)) is True:
        return await message.reply(strings["report_admin"])

    admins = await get_admins_rights(chat["chat_id"])

    offender = await get_user_link(offender_id)
    text = strings["reported_user"].format(user=offender)

    try:
        if message.text.split(None, 2)[1]:
            reason = " ".join(message.text.split(None, 2)[1:])
            text += strings["reported_reason"].format(reason=reason)
    except IndexError:
        pass

    for admin in admins:
        text += await get_user_link(admin, custom_name="​")

    await message.reply(text)
