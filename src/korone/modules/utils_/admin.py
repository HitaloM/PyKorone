from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from aiogram.enums import ChatMemberStatus

from korone.config import CONFIG
from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.repositories.chat import ChatRepository
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.logger import get_logger
from korone.modules.utils_.chat_member import update_chat_members

if TYPE_CHECKING:
    from typing import Any

    from korone.db.models.chat import ChatModel

logger = get_logger(__name__)

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


async def _resolve_model(model_id: int) -> ChatModel | None:
    if model := await ChatRepository.get_by_chat_id(model_id):
        return model
    return await ChatRepository.get_by_id(model_id)


async def _ensure_admin_cache(chat_model: ChatModel) -> None:
    if await ChatAdminRepository.has_admins(chat_model):
        return

    await update_chat_members(chat_model)


async def _get_admin_data(chat_model: ChatModel, user_model: ChatModel) -> dict[str, Any] | None:
    await _ensure_admin_cache(chat_model)
    if admin := await ChatAdminRepository.get_chat_admin(chat_model, user_model):
        return admin.data
    return None


async def check_user_admin_permissions(
    chat: int,
    user: int,
    required_permissions: list[str] | None = None,
    *,
    require_creator: bool = False,
    chat_model: ChatModel | None = None,
    user_model: ChatModel | None = None,
) -> bool | list[str]:
    await logger.adebug(
        "check_user_admin_permissions",
        chat=chat,
        user=user,
        permissions=required_permissions,
        require_creator=require_creator,
    )

    if chat == user and not require_creator:
        return True

    if user in CONFIG.operators and not require_creator:
        return True

    if user == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID and not require_creator:
        return True

    if not chat_model:
        chat_model = await _resolve_model(chat)
    if not chat_model:
        return False

    if not user_model:
        user_model = await _resolve_model(user)
    if not user_model:
        return False

    if not require_creator:
        if chat_model.chat_id == user_model.chat_id:
            return True
        if user_model.chat_id in CONFIG.operators:
            return True
        if user_model.chat_id == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
            return True

    admin_data = await _get_admin_data(chat_model, user_model)
    if not admin_data:
        return False

    if require_creator:
        return _is_creator_status(admin_data.get("status"))

    if not required_permissions:
        return True

    if _is_creator_status(admin_data.get("status")):
        return True

    missing_permissions = [permission for permission in required_permissions if admin_data.get(permission) is not True]

    return missing_permissions or True


def _is_creator_status(status: str | None) -> bool:
    if status is None:
        return False

    try:
        return ChatMemberStatus(status) == ChatMemberStatus.CREATOR
    except ValueError:
        return False


async def is_user_admin(chat: int, user: int) -> bool:
    result = await check_user_admin_permissions(chat, user)
    return result is True


async def is_chat_creator(chat: int, user: int) -> bool:
    chat_model = await _resolve_model(chat)
    if not chat_model:
        return False

    user_model = await _resolve_model(user)
    if not user_model:
        return False

    admin_data = await _get_admin_data(chat_model, user_model)
    if not admin_data:
        return False

    admin_status = admin_data.get("status")
    if not admin_status:
        return False

    try:
        return ChatMemberStatus(admin_status) == ChatMemberStatus.CREATOR
    except ValueError:
        return False


async def get_admins_rights(chat: int, *, force_update: bool = False) -> None:
    chat_model = await _resolve_model(chat)
    if not chat_model:
        return

    if force_update or not await ChatAdminRepository.has_admins(chat_model):
        await update_chat_members(chat_model)
