import datetime
import html
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from sophie_bot.services.db import db
from sophie_bot.utils.logger import log


async def update_user(chat_id, new_user):
    old_user = await db.user_list.find_one({"user_id": new_user.iid})

    new_chat = [chat_id]

    if old_user and "chats" in old_user:
        if old_user["chats"]:
            new_chat = old_user["chats"]
        if not new_chat or chat_id not in new_chat:
            new_chat.append(chat_id)

    if old_user and "first_detected_date" in old_user:
        first_detected_date = old_user["first_detected_date"]
    else:
        first_detected_date = datetime.datetime.now()

    if new_user.username:
        username = new_user.username.lower()
    else:
        username = None

    if hasattr(new_user, "last_name") and new_user.last_name:
        last_name = html.escape(new_user.last_name, quote=False)
    else:
        last_name = None

    first_name = html.escape(new_user.first_name, quote=False)

    user_new = {
        "user_id": new_user.iid,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "user_lang": new_user.language_code,
        "chats": new_chat,
        "first_detected_date": first_detected_date,
    }

    # Check on old user in DB with same username
    find_old_user = {
        "username": user_new["username"],
        "user_id": {"$ne": user_new["user_id"]},
    }
    if user_new["username"] and (check := await db.user_list.find_one(find_old_user)):
        await db.user_list.delete_one({"_id": check["_id"]})
        log.info(
            f"Found user ({check['user_id']}) with same username as ({user_new['user_id']}), old user was deleted."
        )

    await db.user_list.update_one({"user_id": new_user.iid}, {"$set": user_new}, upsert=True)

    log.debug(f"Users: User {new_user.iid} updated")

    return user_new


class LegacySaveChats(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: dict[str, Any],
    ) -> Any:
        log.debug('Middleware "LegacySaveChats"')
        chat_id = message.chat.id

        # Update chat
        new_chat = message.chat
        if not new_chat.type == "private":
            old_chat = await db.chat_list.find_one({"chat_id": chat_id})

            if not hasattr(new_chat, "username"):
                chatnick = None
            else:
                chatnick = new_chat.username

            if old_chat and "first_detected_date" in old_chat:
                first_detected_date = old_chat["first_detected_date"]
            else:
                first_detected_date = datetime.datetime.now()

            chat_new = {
                "chat_id": chat_id,
                "chat_title": html.escape(new_chat.title, quote=False),
                "chat_nick": chatnick,
                "type": new_chat.type,
                "first_detected_date": first_detected_date,
            }

            # Check on old chat in DB with same username
            find_old_chat = {
                "chat_nick": chat_new["chat_nick"],
                "chat_id": {"$ne": chat_new["chat_id"]},
            }
            if chat_new["chat_nick"] and (check := await db.chat_list.find_one(find_old_chat)):
                await db.chat_list.delete_one({"_id": check["_id"]})
                log.info(
                    f"Found chat ({check['chat_id']}) with same username as "
                    f"({chat_new['chat_id']}), old chat was deleted."
                )

            await db.chat_list.update_one({"chat_id": chat_id}, {"$set": chat_new}, upsert=True)

            log.debug(f"Users: Chat {chat_id} updated")

        # Update users
        await update_user(chat_id, message.from_user)

        if (
            message.reply_to_message
            and hasattr(message.reply_to_message.from_user, "chat_id")
            and message.reply_to_message.from_user.chat_id
        ):
            await update_user(chat_id, message.reply_to_message.from_user)

        if message.forward_from:
            await update_user(chat_id, message.forward_from)

        log.debug('Middleware "LegacySaveChats" done')
        return await handler(message, data)
