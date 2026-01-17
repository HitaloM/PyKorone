from __future__ import annotations

from typing import Literal, Optional, Union

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from sophie_bot.config import CONFIG
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel
from sophie_bot.modules.utils_.chat_member import update_chat_members
from sophie_bot.utils.logger import log

# Telegram's anonymous admin bot ID
ANONYMOUS_ADMIN_BOT_ID = 1087968824

# Type alias for admin permissions
AdminPermission = Literal[
    "can_post_messages",
    "can_edit_messages",
    "can_delete_messages",
    "can_restrict_members",
    "can_promote_members",
    "can_change_info",
    "can_invite_users",
    "can_pin_messages",
]


async def check_user_admin_permissions(
    chat_tid: int,
    user_tid: int,
    required_permissions: Optional[list[str]] = None,
) -> Union[bool, str]:
    """
    Check if a user is an admin in the specified chat and has the required permissions.

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to check
        required_permissions: Optional list of permissions to check (e.g., ["can_restrict_members"])

    Returns:
        True if the user is an admin with all required permissions.
        The missing permission name (str) if a specific permission is missing.
        False if the user is not an admin at all.
    """
    log.debug("check_user_admin_permissions", chat_tid=chat_tid, user_tid=user_tid, permissions=required_permissions)

    # User's PM should have admin rights
    if chat_tid == user_tid:
        return True

    # Bot operators always have admin rights with all permissions
    if user_tid in CONFIG.operators:
        return True

    # Workaround to support anonymous admins - they have all permissions
    if user_tid == ANONYMOUS_ADMIN_BOT_ID:
        return True

    # Check database for admin status
    try:
        chat = await ChatModel.get_by_tid(chat_tid)
        if not chat:
            return False

        user = await ChatModel.get_by_tid(user_tid)
        if not user:
            return False

        admin = await ChatAdminModel.find_one(
            ChatAdminModel.chat.id == chat.iid,  # type: ignore
            ChatAdminModel.user.id == user.iid,  # type: ignore
        )

        if not admin:
            return False

        # If no specific permissions required, just check admin status
        if not required_permissions:
            return True

        # Chat creator has all permissions
        if admin.member.status == ChatMemberStatus.CREATOR:
            return True

        # Check each required permission
        for permission in required_permissions:
            permission_value = getattr(admin.member, permission, None)
            if permission_value is None or permission_value is False:
                return permission

        return True

    except TelegramBadRequest as err:
        # Handle case when function is called outside of a group
        if "there are no administrators in the private chat" in str(err):
            return False
        raise


async def is_user_admin(chat_tid: int, user_tid: int) -> bool:
    """
    Check if a user is an admin in the specified chat.

    This is a convenience wrapper around check_user_admin_permissions
    that only checks admin status without specific permissions.

    Args:
        chat_tid: Telegram chat ID
        user_tid: Telegram user ID to check

    Returns:
        True if the user is an admin, False otherwise
    """
    result = await check_user_admin_permissions(chat_tid, user_tid)
    return result is True


async def is_chat_creator(chat_tid: int, user_tid: int) -> bool:
    """Check if the user is the creator of the chat."""
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        return False

    user = await ChatModel.get_by_tid(user_tid)
    if not user:
        return False

    admin = await ChatAdminModel.find_one(
        ChatAdminModel.chat.id == chat.iid,  # type: ignore
        ChatAdminModel.user.id == user.iid,  # type: ignore
    )
    if not admin:
        return False

    return admin.member.status == ChatMemberStatus.CREATOR


async def get_admins_rights(chat_tid: int, force_update: bool = False) -> None:
    """Refresh admin cache for the chat (wrapper for update_chat_admins)."""
    # This seems to map to logic that updates admins in DB.
    # Assuming update_chat_admins is the modern equivalent if it exists or we implement logic here.
    # For now, we can check if update_chat_members handles admins or if there is a specific function.
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        return

    await update_chat_members(chat)
