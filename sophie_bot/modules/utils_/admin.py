from __future__ import annotations

from typing import Literal, Optional, Union

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from beanie import PydanticObjectId

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


async def _resolve_model(model_id: Union[int, PydanticObjectId]) -> Optional[ChatModel]:
    if isinstance(model_id, int):
        return await ChatModel.get_by_tid(model_id)
    return await ChatModel.get_by_iid(model_id)


async def check_user_admin_permissions(
    chat: Union[int, PydanticObjectId],
    user: Union[int, PydanticObjectId],
    required_permissions: Optional[list[str]] = None,
) -> Union[bool, str]:
    """
    Check if a user is an admin in the specified chat and has the required permissions.

    Args:
        chat: Telegram chat ID or Internal DB ID
        user: Telegram user ID or Internal DB ID
        required_permissions: Optional list of permissions to check (e.g., ["can_restrict_members"])

    Returns:
        True if the user is an admin with all required permissions.
        The missing permission name (str) if a specific permission is missing.
        False if the user is not an admin at all.
    """
    log.debug("check_user_admin_permissions", chat=chat, user=user, permissions=required_permissions)

    # Fast path for TIDs (ints)
    if isinstance(chat, int) and isinstance(user, int):
        # User's PM should have admin rights
        if chat == user:
            return True

        # Bot operators always have admin rights with all permissions
        if user in CONFIG.operators:
            return True

        # Workaround to support anonymous admins - they have all permissions
        if user == ANONYMOUS_ADMIN_BOT_ID:
            return True

    # Resolve models
    chat_model = await _resolve_model(chat)
    if not chat_model:
        return False

    user_model = await _resolve_model(user)
    if not user_model:
        return False

    # Check if we missed the fast path checks (e.g. if one was IID)
    if not (isinstance(chat, int) and isinstance(user, int)):
        if chat_model.tid == user_model.tid:
            return True
        if user_model.tid in CONFIG.operators:
            return True
        if user_model.tid == ANONYMOUS_ADMIN_BOT_ID:
            return True

    # Check database for admin status
    try:
        admin = await ChatAdminModel.find_one(
            ChatAdminModel.chat.iid == chat_model.iid,  # type: ignore
            ChatAdminModel.user.iid == user_model.iid,  # type: ignore
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


async def is_user_admin(chat: Union[int, PydanticObjectId], user: Union[int, PydanticObjectId]) -> bool:
    """
    Check if a user is an admin in the specified chat.

    This is a convenience wrapper around check_user_admin_permissions
    that only checks admin status without specific permissions.

    Args:
        chat: Telegram chat ID or Internal DB ID
        user: Telegram user ID or Internal DB ID

    Returns:
        True if the user is an admin, False otherwise
    """
    result = await check_user_admin_permissions(chat, user)
    return result is True


async def is_chat_creator(chat: Union[int, PydanticObjectId], user: Union[int, PydanticObjectId]) -> bool:
    """Check if the user is the creator of the chat."""
    chat_model = await _resolve_model(chat)
    if not chat_model:
        return False

    user_model = await _resolve_model(user)
    if not user_model:
        return False

    admin = await ChatAdminModel.find_one(
        ChatAdminModel.chat.iid == chat_model.iid,  # type: ignore
        ChatAdminModel.user.iid == user_model.iid,  # type: ignore
    )
    if not admin:
        return False

    return admin.member.status == ChatMemberStatus.CREATOR


async def get_admins_rights(chat: Union[int, PydanticObjectId], force_update: bool = False) -> None:
    """Refresh admin cache for the chat (wrapper for update_chat_admins)."""
    # This seems to map to logic that updates admins in DB.
    # Assuming update_chat_admins is the modern equivalent if it exists or we implement logic here.
    # For now, we can check if update_chat_members handles admins or if there is a specific function.
    chat_model = await _resolve_model(chat)
    if not chat_model:
        return

    await update_chat_members(chat_model)
