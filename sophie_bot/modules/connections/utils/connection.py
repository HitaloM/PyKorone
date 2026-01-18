from datetime import datetime, timedelta, timezone
from typing import Optional

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from stfu_tg import Doc, Section, Template, Title

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_connection_settings import ChatConnectionSettingsModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.modules.connections.utils.constants import CONNECTION_DISCONNECT_TEXT
from sophie_bot.modules.connections.utils.texts import CONNECTION_OBSOLETE_NOTICE
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.services.redis import redis
from sophie_bot.utils.i18n import gettext as _


async def set_connected_chat(user_id: int, chat_id: Optional[int]):
    """
    Connects user to a chat.
    If chat_id is None, disconnects.
    Sets expiry to 48 hours from now.
    """
    # Clear legacy redis cache just in case
    redis.delete(f"connection_cache_{user_id}")

    if chat_id is None:
        if conn := await ChatConnectionModel.find_one(ChatConnectionModel.user_id == user_id):
            conn.chat_id = None
            conn.expires_at = None
            await conn.save()
        return

    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

    conn = await ChatConnectionModel.find_one(ChatConnectionModel.user_id == user_id)
    if conn:
        conn.chat_id = chat_id
        conn.expires_at = expires_at
        if chat_id not in conn.history:
            conn.history.append(chat_id)
        await conn.save()
    else:
        conn = ChatConnectionModel(user_id=user_id, chat_id=chat_id, expires_at=expires_at, history=[chat_id])
        await conn.insert()


async def check_connection_permissions(chat_id: int, user_id: int) -> bool:
    """
    Checks if a user is allowed to connect to a chat.
    Admins are always allowed.
    Normal users are allowed if 'allow_users_connect' is enabled in settings.
    """
    # Admins always allowed
    if await is_user_admin(chat_id, user_id):
        return True

    # Check settings
    settings = await ChatConnectionSettingsModel.get_by_chat_id(chat_id)
    if settings and not settings.allow_users_connect:
        return False

    return True


async def get_connection_text(chat_id: int) -> Doc:
    """Returns the formatted document for a successful connection."""
    chat = await ChatModel.get_by_tid(chat_id)
    return Doc(
        Title(_("Connected!")),
        Template(_("Connected to {chat_name}."), chat_name=chat.first_name_or_title if chat else str(chat_id)),
        Section(
            _("Notices"),
            CONNECTION_OBSOLETE_NOTICE,
            _("⏳ This connection will last for 48 hours."),
        ),
    )


def get_disconnect_markup() -> ReplyKeyboardMarkup:
    """Returns the reply keyboard markup with the disconnect button."""
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=str(CONNECTION_DISCONNECT_TEXT))]], resize_keyboard=True)
