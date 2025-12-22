# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
import datetime
import html
import pickle
import re
from contextlib import suppress
from typing import Union

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, MessageEntity

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.legacy_modules.utils.message import get_arg, get_args_str
from sophie_bot.services.bot import bot
from sophie_bot.services.db import db
from sophie_bot.services.redis import bredis
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log
from .language import get_string
from ...utils_.user_details import save_chat_member


async def get_user_by_id(user_id: int):
    if not user_id <= 9223372036854775807:  # int64
        return None

    user = await db.user_list.find_one({"user_id": user_id})
    if not user:
        return None

    return user


async def get_user_by_username(username):
    # Search username in database
    if "@" in username:
        # Remove '@'
        username = username[1:]

    user = await db.user_list.find_one({"username": username.lower()})

    # Ohnu, we don't have this user in DB
    if not user:
        return None

    return user


async def get_user_link(user_id, custom_name=None, md=False, escape_html=True):
    user = await db.user_list.find_one({"user_id": user_id})

    if user:
        user_name = user["first_name"]
    else:
        user_name = str(user_id)

    if custom_name:
        user_name = custom_name

    if not md and escape_html:
        user_name = html.escape(user_name, quote=False)

    if md:
        return "[{name}](tg://user?id={id})".format(name=user_name, id=user_id)
    else:
        return '<a href="tg://user?id={id}">{name}</a>'.format(name=user_name, id=user_id)


async def get_admins_rights(chat_id, force_update=False):
    chat = await ChatModel.get_by_tid(chat_id)

    key = "admin_cache:" + str(chat_id)
    if (alist := bredis.get(key)) and not force_update:
        return pickle.loads(alist)
    else:
        alist = {}
        chat_members = await bot.get_chat_administrators(chat_id)
        for member in chat_members:
            if not member:
                continue

            user_id = member.user.id
            alist[user_id] = {
                "status": member.status,
                "admin": True,
                "title": member.custom_title,
                "anonymous": member.is_anonymous,
                "can_change_info": member.can_change_info if member.status != ChatMemberStatus.CREATOR else True,
                "can_delete_messages": member.can_delete_messages
                if member.status != ChatMemberStatus.CREATOR
                else True,
                "can_invite_users": member.can_invite_users if member.status != ChatMemberStatus.CREATOR else True,
                "can_restrict_members": (
                    member.can_restrict_members if member.status != ChatMemberStatus.CREATOR else True
                ),
                "can_pin_messages": member.can_pin_messages if member.status != ChatMemberStatus.CREATOR else True,
                "can_promote_members": member.can_promote_members
                if member.status != ChatMemberStatus.CREATOR
                else True,
            }

            with suppress(KeyError):  # Optional permissions
                alist[user_id]["can_post_messages"] = (
                    member.can_post_messages if member.status != ChatMemberStatus.CREATOR else True
                )

            # Workaround for modern chat_admin db
            user = await ChatModel.get_by_tid(chat_id)
            if not user:
                continue
            await save_chat_member(chat.id, user.id, member)

        bredis.set(key, pickle.dumps(alist))
        bredis.expire(key, 900)

    return alist


async def is_user_admin(chat_id, user_id):
    log.debug("is_user_admin", chat_id=chat_id, user_id=user_id)

    # User's pm should have admin rights
    if chat_id == user_id:
        return True

    if user_id in CONFIG.operators:
        return True

    # Workaround to support anonymous admins
    if user_id == 1087968824:
        return True

    try:
        admins = await get_admins_rights(chat_id)
        if user_id in admins:
            return True
        else:
            return False

    # Workaround when the function is being called not in the group
    # aiogram.exceptions.TelegramBadRequest: Telegram server says - Bad Request: there are no administrators in the private chat
    except TelegramBadRequest as err:
        if "there are no administrators in the private chat" in err.message:
            return False
        raise err


async def check_admin_rights(event: Union[Message, CallbackQuery], chat_id, user_id, rights):
    # User's pm should have admin rights
    if chat_id == user_id:
        return True

    if user_id in CONFIG.operators:
        return True

    # Workaround to support anonymous admins
    if user_id == 1087968824:
        if not isinstance(event, Message):
            raise ValueError(f"Cannot extract signuature of anonymous admin from {type(event)}")

        if not event.author_signature:
            return True

        for admin in (await get_admins_rights(chat_id)).values():
            if "title" in admin and admin["title"] == event.author_signature:
                for permission in rights:
                    if not admin[permission]:
                        return permission
        return True

    admin_rights = await get_admins_rights(chat_id)
    if user_id not in admin_rights:
        return False

    if admin_rights[user_id]["status"] == "creator":
        return True

    for permission in rights:
        if not admin_rights[user_id][permission]:
            return permission

    return True


async def is_chat_creator(event: Union[Message, CallbackQuery], chat_id, user_id):
    admin_rights = await get_admins_rights(chat_id)

    if user_id == 1087968824:
        _co, possible_creator = 0, None
        for admin in admin_rights.values():
            if admin["title"] == event.author_signature:
                _co += 1
                possible_creator = admin

        if _co > 1:
            await event.answer(await get_string(chat_id, "global", "unable_identify_creator"))
            raise SkipHandler

        if possible_creator["status"] == "creator":
            return True
        return False

    if user_id not in admin_rights:
        return False

    if admin_rights[user_id]["status"] == "creator":
        return True

    return False


async def get_user_by_text(message: Message, text: str):
    # Get all entities
    entities: list[MessageEntity] = (
        list(
            filter(
                lambda ent: ent.type == "text_mention" or ent.type == "mention",
                message.entities,
            )
        )
        if message.entities
        else []
    )
    for entity in entities:
        # If username matches entity's text
        if text in entity.extract_from(message.text):
            if entity.type == "mention":
                # This one entity is comes with mention by username, like @rSophieBot
                return await get_user_by_username(text)
            elif entity.type == "text_mention":
                # This one is link mention, mostly used for users without an username
                return await get_user_by_id(entity.user.id)

    # Now let's try get user with user_id
    # We trying this not first because user link mention also can have numbers
    if text.isdigit():
        user_id = int(text)
        if user := await get_user_by_id(user_id):
            return user

    # Not found anything 😞
    return None


async def get_user(message, allow_self=False):
    args = message.text.split(None, 2)
    user = None

    # Only 1 way
    if len(args) < 2 and message.reply_to_message:
        return await get_user_by_id(message.reply_to_message.from_user.id)

    # Use default function to get user
    if len(args) > 1:
        user = await get_user_by_text(message, args[1])

    if not user and bool(message.reply_to_message):
        user = await get_user_by_id(message.reply_to_message.from_user.id)

    if not user and allow_self:
        # TODO: Fetch user from message instead of db?! less overhead
        return await get_user_by_id(message.from_user.id)

    # No args and no way to get user
    if not user and len(args) < 2:
        return None

    return user


async def get_user_and_text(message, **kwargs):
    args = message.text.split(" ", 2)
    user = await get_user(message, **kwargs)

    if len(args) > 1:
        if (test_user := await get_user_by_text(message, args[1])) == user:
            if test_user:
                print(len(args))
                if len(args) > 2:
                    return user, args[2]
                else:
                    return user, ""

    if len(args) > 1:
        return user, message.text.split(" ", 1)[1]
    else:
        return user, ""


def get_user_and_text_dec(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, "message"):
                message = message.message

            user, text = await get_user_and_text(message, **dec_kwargs)
            if not user:
                await message.reply("I can't get the user!")
                return
            else:
                return await func(*args, user, text, **kwargs)

        return wrapped_1

    return wrapped


def get_user_dec(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, "message"):
                message = message.message

            user, text = await get_user_and_text(message, **dec_kwargs)
            if not bool(user):
                await message.reply("I can't get the user!")
                return
            else:
                return await func(*args, user, **kwargs)

        return wrapped_1

    return wrapped


def get_chat_dec(allow_self=False, fed=False):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, "message"):
                message = message.message

            arg = get_arg(message)
            if fed is True:
                if len(text := get_args_str(message).split()) > 1:
                    if text[0].count("-") == 4:
                        arg = text[1]
                    else:
                        arg = text[0]

            if arg.startswith("-") or arg.isdigit():
                chat = await db.chat_list.find_one({"chat_id": int(arg)})
                if not chat:
                    try:
                        # Here is a workaround for aiogram 3.0, which changed dictionaries to objects
                        if chat_request := await bot.get_chat(arg):
                            chat = {
                                "chat_id": chat_request.id,
                                "chat_type": chat_request.type,
                                "chat_title": chat_request.title,
                                "chat_nick": chat_request.username,
                                "first_detected_date": datetime.datetime.now(),
                                "type": chat_request.type,
                            }
                    except TelegramBadRequest:
                        await message.reply(
                            _("I couldn't find the chat / channel! Please ensure that I am added as an admin there!")
                        )
                        return
            elif arg.startswith("@"):
                chat = await db.chat_list.find_one({"chat_nick": re.compile(arg.strip("@"), re.IGNORECASE)})
            elif allow_self is True:
                chat = await db.chat_list.find_one({"chat_id": message.chat.id})
            else:
                await message.reply(_("Please give me valid chat ID/username"))
                return

            if not chat:
                await message.reply(_("I can't find any chats on given information!"))
                return

            return await func(*args, chat, **kwargs)

        return wrapped_1

    return wrapped
