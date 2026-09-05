from typing import TYPE_CHECKING

from aiogram.enums import ChatMemberStatus

from korone.config import CONFIG
from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.repositories.chat import ChatRepository
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.logger import get_logger
from korone.modules.utils_.chat_member import update_chat_members

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    from korone.db.models.chat import ChatModel

logger = get_logger(__name__)


def check_member_permissions(
    member_data: Mapping[str, object], required_permissions: Sequence[str] = (), *, require_creator: bool = False
) -> bool | list[str]:
    is_creator = member_data.get("status") == ChatMemberStatus.CREATOR
    if require_creator:
        return is_creator
    if is_creator:
        return True
    missing = [permission for permission in required_permissions if member_data.get(permission) is not True]
    return missing or True


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
        chat_model = await ChatRepository.get_by_chat_id(chat)
    if not chat_model:
        return False

    if not user_model:
        user_model = await ChatRepository.get_by_chat_id(user)
    if not user_model:
        return False

    admin_data = await _get_admin_data(chat_model, user_model)
    if not admin_data:
        return False

    return check_member_permissions(admin_data, required_permissions or (), require_creator=require_creator)


async def is_user_admin(chat: int, user: int) -> bool:
    result = await check_user_admin_permissions(chat, user)
    return result is True


async def is_chat_creator(chat: int, user: int) -> bool:
    result = await check_user_admin_permissions(chat, user, require_creator=True)
    return result is True


async def get_admins_rights(chat: int, *, force_update: bool = False) -> None:
    chat_model = await ChatRepository.get_by_chat_id(chat)
    if not chat_model:
        return

    if force_update or not await ChatAdminRepository.has_admins(chat_model):
        await update_chat_members(chat_model)
