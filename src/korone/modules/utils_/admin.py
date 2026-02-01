from __future__ import annotations

import json
from typing import Literal

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from korone import aredis
from korone.config import CONFIG
from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.models.chat import ChatModel
from korone.logging import get_logger
from korone.modules.utils_.chat_member import update_chat_members

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
    if model := await ChatModel.get_by_id(model_id):
        return model
    return await ChatModel.get_by_tid(model_id)


async def check_user_admin_permissions(
    chat: int, user: int, required_permissions: list[str] | None = None
) -> bool | list[str]:
    await logger.adebug("check_user_admin_permissions", chat=chat, user=user, permissions=required_permissions)

    if isinstance(chat, int) and isinstance(user, int):
        if chat == user:
            return True

        if user in CONFIG.operators:
            return True

        if user == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
            return True

    chat_model = await _resolve_model(chat)
    if not chat_model:
        return False

    user_model = await _resolve_model(user)
    if not user_model:
        return False

    if chat_model.id == user_model.id:
        return True
    if user_model.id in CONFIG.operators:
        return True
    if user_model.id == TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
        return True
    try:
        cache_key = f"chat_admins:{chat_model.tid}"
        raw = await aredis.get(cache_key)

        if raw is None:
            await update_chat_members(chat_model)
            raw = await aredis.get(cache_key)

        if not raw:
            return False

        try:
            admins = json.loads(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
        except TypeError, UnicodeDecodeError, json.JSONDecodeError:
            await logger.adebug("check_user_admin_permissions: invalid admins cache", key=cache_key)
            return False

        admin_data = admins.get(str(user_model.tid))
        if not admin_data:
            return False

        if not required_permissions:
            return True

        admin_status = admin_data.get("status")
        if admin_status == ChatMemberStatus.CREATOR or admin_status == ChatMemberStatus.CREATOR.value:
            return True

        missing_permissions = []
        for permission in required_permissions:
            permission_value = admin_data.get(permission)
            if permission_value is None or permission_value is False:
                missing_permissions.append(permission)

        return missing_permissions or True

    except TelegramBadRequest as err:
        if "there are no administrators in the private chat" in str(err):
            return False
        raise


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

    cache_key = f"chat_admins:{chat_model.tid}"
    raw = await aredis.get(cache_key)
    if raw is None:
        await update_chat_members(chat_model)
        raw = await aredis.get(cache_key)
    if not raw:
        return False
    try:
        admins = json.loads(raw.decode() if isinstance(raw, (bytes, bytearray)) else raw)
    except TypeError, UnicodeDecodeError, json.JSONDecodeError:
        await logger.adebug("is_chat_creator: invalid admins cache", key=cache_key)
        return False

    admin_data = admins.get(str(user_model.tid))
    if not admin_data:
        return False

    admin_status = admin_data.get("status")
    return admin_status == ChatMemberStatus.CREATOR or admin_status == ChatMemberStatus.CREATOR.value


async def get_admins_rights(chat: int, *, force_update: bool = False) -> None:
    chat_model = await _resolve_model(chat)
    if not chat_model:
        return

    await update_chat_members(chat_model)
