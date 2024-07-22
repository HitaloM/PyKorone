from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramMigrateToChat,
    TelegramUnauthorizedError,
)
from aiogram.types.chat_permissions import ChatPermissions

from sophie_bot import bot


async def ban_user(chat_id, user_id, until_date=None):
    try:
        await bot.ban_chat_member(chat_id, user_id, until_date=until_date)
    except (TelegramBadRequest, TelegramMigrateToChat, TelegramUnauthorizedError):
        return False
    return True


async def kick_user(chat_id, user_id):
    await bot.unban_chat_member(chat_id, user_id)
    return True


async def mute_user(chat_id, user_id, until_date=None):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(can_send_messages=False, until_date=until_date),
        until_date=until_date,
    )
    return True


async def restrict_user(chat_id, user_id, until_date=None):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            until_date=until_date,
        ),
        until_date=until_date,
    )
    return True


async def unmute_user(chat_id, user_id):
    await bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        ),
    )
    return True


async def unban_user(chat_id, user_id):
    try:
        return await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    except (TelegramBadRequest, TelegramUnauthorizedError):
        return False
