from __future__ import annotations

from datetime import timedelta
from typing import Optional

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError
from aiogram.types import ChatPermissions

from sophie_bot.services.bot import bot
from sophie_bot.utils.logger import log


async def ban_user(chat_tid: int, user_tid: int, until_date: Optional[timedelta] = None) -> bool:
    """
    Ban a user from the chat.

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to ban
        until_date: Optional duration for the ban (None = permanent)

    Returns:
        True if successful, False if failed
    """
    try:
        await bot.ban_chat_member(chat_tid, user_tid, until_date=until_date)
        return True
    except (TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError) as err:
        log.warning("Failed to ban user", chat_tid=chat_tid, user_tid=user_tid, error=str(err))
        return False


async def kick_user(chat_tid: int, user_tid: int) -> bool:
    """
    Kick a user from the chat (removes but allows rejoining).

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to kick

    Returns:
        True if successful, False if failed
    """
    try:
        await bot.unban_chat_member(chat_tid, user_tid)
        return True
    except (TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError) as err:
        log.warning("Failed to kick user", chat_tid=chat_tid, user_tid=user_tid, error=str(err))
        return False


async def mute_user(chat_tid: int, user_tid: int, until_date: Optional[timedelta] = None) -> bool:
    """
    Mute a user in the chat (restrict sending messages).

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to mute
        until_date: Optional duration for the mute (None = permanent)

    Returns:
        True if successful, False if failed
    """
    try:
        await bot.restrict_chat_member(
            chat_tid,
            user_tid,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date,
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError) as err:
        log.warning("Failed to mute user", chat_tid=chat_tid, user_tid=user_tid, error=str(err))
        return False


async def unmute_user(chat_tid: int, user_tid: int) -> bool:
    """
    Unmute a user in the chat (restore message sending permissions).

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to unmute

    Returns:
        True if successful, False if failed
    """
    try:
        await bot.restrict_chat_member(
            chat_tid,
            user_tid,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError) as err:
        log.warning("Failed to unmute user", chat_tid=chat_tid, user_tid=user_tid, error=str(err))
        return False


async def unban_user(chat_tid: int, user_tid: int) -> bool:
    """
    Unban a user from the chat.

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to unban

    Returns:
        True if successful, False if failed
    """
    try:
        await bot.unban_chat_member(chat_tid, user_tid, only_if_banned=True)
        return True
    except (TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError) as err:
        log.warning("Failed to unban user", chat_tid=chat_tid, user_tid=user_tid, error=str(err))
        return False


async def restrict_user(chat_tid: int, user_tid: int, until_date: Optional[timedelta] = None) -> bool:
    """
    Restrict a user in the chat (allow text messages only, no media).

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to restrict
        until_date: Optional duration for the restriction (None = permanent)

    Returns:
        True if successful, False if failed
    """
    try:
        await bot.restrict_chat_member(
            chat_tid,
            user_tid,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
            until_date=until_date,
        )
        return True
    except (TelegramBadRequest, TelegramForbiddenError, TelegramUnauthorizedError) as err:
        log.warning("Failed to restrict user", chat_tid=chat_tid, user_tid=user_tid, error=str(err))
        return False
