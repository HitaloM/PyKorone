from aiogram.types import Message

from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.utils.i18n import gettext as _


async def get_connected_chat(message: Message, admin=False, only_groups=False):
    user_id = message.from_user.id
    chat = message.chat

    if chat.type != "private":
        conn = await ConnectionsMiddleware.get_current_chat_info(chat)
    else:
        from sophie_bot.db.models.chat_connections import ChatConnectionModel

        connection = await ChatConnectionModel.get_by_user_id(user_id)
        if connection and connection.chat_id:
            conn = await ConnectionsMiddleware.get_chat_from_db(connection.chat_id, True)
        else:
            conn = await ConnectionsMiddleware.get_current_chat_info(chat)

    if not conn:
        return None

    res = {
        "chat_id": conn.tid,
        "title": conn.title,
        "type": conn.type.value if hasattr(conn.type, "value") else conn.type,
        "connection": conn.is_connected,
    }

    if admin:
        if not await is_user_admin(res["chat_id"], user_id):
            await message.reply(_("You must be an admin to use this command in the connected chat."))
            return None

    if only_groups and res["type"] == "private":
        await message.reply(_("This command can only be used in groups."))
        return None

    return res


def chat_connection(admin=False, only_groups=False):
    def decorator(func):
        async def wrapper(message, *args, **kwargs):
            if isinstance(message, Message):
                chat = await get_connected_chat(message, admin=admin, only_groups=only_groups)
                if not chat:
                    return
                # Check if func expects 'chat' arg?
                # Legacy register probably passed args based on signature or just kwargs.
                # But here we assume we pass 'chat' as second arg or kwarg.
                # Looking at legacy reports.py: async def report(message, chat, strings)
                # usage: @chat_connection... def report1_cmd(message, chat, strings)
                # So we pass chat.
                return await func(message, chat, *args, **kwargs)
            else:
                return await func(message, *args, **kwargs)

        return wrapper

    return decorator
