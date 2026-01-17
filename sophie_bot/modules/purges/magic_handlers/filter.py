from aiogram.types import Message

from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.i18n import lazy_gettext as l_


async def delmsg_filter_handle(message: Message, chat, data):
    if not message.from_user:
        return

    if await is_user_admin(data["chat_id"], message.from_user.id):
        return

    await common_try(message.delete())


def get_filter():
    return {
        "delete_message": {
            "title": l_("🗑 Delete message"),
            "handle": delmsg_filter_handle,
            "del_btn_name": lambda msg, data: f"Del message: {data['handler']}",
        }
    }
