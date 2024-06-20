import datetime

from sophie_bot.modules.legacy_modules.modules import LOADED_MODULES
from sophie_bot.modules.legacy_modules.utils.connections import chat_connection
from sophie_bot.modules.legacy_modules.utils.disable import disableable_dec
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.modules.legacy_modules.utils.user_details import (
    get_admins_rights,
    get_user_dec,
    get_user_link,
    is_user_admin,
)
from sophie_bot.services.db import db


@register(cmds="info")
@disableable_dec("info")
@get_user_dec(allow_self=True)
@get_strings_dec("users")
async def user_info(message, user, strings):
    chat_id = message.chat.id

    text = strings["user_info"]
    text += strings["info_id"].format(id=user["user_id"])
    text += strings["info_first"].format(first_name=str(user["first_name"]))

    if user["last_name"] is not None:
        text += strings["info_last"].format(last_name=str(user["last_name"]))

    if user["username"] is not None:
        text += strings["info_username"].format(username="@" + str(user["username"]))

    text += strings["info_link"].format(user_link=str(await get_user_link(user["user_id"])))

    text += "\n"

    if await is_user_admin(chat_id, user["user_id"]) is True:
        text += strings["info_admeme"]

    for module in [m for m in LOADED_MODULES if hasattr(m, "__user_info__")]:
        if txt := await module.__user_info__(message, user["user_id"]):
            text += txt

    text += strings["info_saw"].format(num=len(user["chats"]) if "chats" in user else 0)

    await message.reply(text)


@register(cmds="admincache", is_admin=True)
@chat_connection(only_groups=True, admin=True)
@get_strings_dec("users")
async def reset_admins_cache(message, chat, strings):
    await get_admins_rights(chat["chat_id"], force_update=True)  # Reset a cache
    await message.reply(strings["upd_cache_done"])


@register(cmds=["id", "chatid", "userid"])
@disableable_dec("id")
@get_user_dec(allow_self=True)
@get_strings_dec("misc")
@chat_connection()
async def get_id(message, user, strings, chat):
    user_id = message.from_user.id

    text = strings["your_id"].format(id=user_id)
    if message.chat.id != user_id:
        text += strings["chat_id"].format(id=message.chat.id)

    if chat["status"] is True:
        text += strings["conn_chat_id"].format(id=chat["chat_id"])

    if not user["user_id"] == user_id:
        text += strings["user_id"].format(user=await get_user_link(user["user_id"]), id=user["user_id"])

    if (
        "reply_to_message" in message
        and "forward_from" in message.reply_to_message
        and not message.reply_to_message.forward_from.id == message.reply_to_message.from_user.id
    ):
        text += strings["user_id"].format(
            user=await get_user_link(message.reply_to_message.forward_from.id),
            id=message.reply_to_message.forward_from.id,
        )

    await message.reply(text)


@register(cmds=["adminlist", "admins"])
@disableable_dec("adminlist")
@chat_connection(only_groups=True)
@get_strings_dec("users")
async def adminlist(message, chat, strings):
    admins = await get_admins_rights(chat["chat_id"])
    text = strings["admins"]
    for admin, rights in admins.items():
        if rights["anonymous"]:
            continue
        text += "- {} ({})\n".format(await get_user_link(admin), admin)

    await message.reply(text, disable_notification=True)


async def __stats__():
    text = "* <code>{}</code> total users, in <code>{}</code> chats\n".format(
        await db.user_list.count_documents({}), await db.chat_list.count_documents({})
    )

    text += "* <code>{}</code> new users and <code>{}</code> new chats in the last 48 hours\n".format(
        await db.user_list.count_documents(
            {"first_detected_date": {"$gte": datetime.datetime.now() - datetime.timedelta(days=2)}}
        ),
        await db.chat_list.count_documents(
            {"first_detected_date": {"$gte": datetime.datetime.now() - datetime.timedelta(days=2)}}
        ),
    )

    return text
