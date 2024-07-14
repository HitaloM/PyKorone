from aiogram.filters import Filter
from aiogram.types import Message

from sophie_bot.config import CONFIG
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin


class IsAdmin(Filter):
    key = "is_admin"

    def __init__(self, is_admin):
        self.is_admin = is_admin

    @get_strings_dec("global")
    async def __call__(self, event, strings, *args, **kwargs):

        if hasattr(event, "message"):
            chat_id = event.message.chat.id
        else:
            chat_id = event.chat.id

        if not await is_user_admin(chat_id, event.from_user.id):
            task = event.answer if hasattr(event, "message") else event.reply
            await task(strings["u_not_admin"])
            return False
        return True


class IsOwner(Filter):
    key = "is_owner"

    def __init__(self, is_owner):
        self.is_owner = is_owner

    async def __call__(self, message: Message):
        if message.from_user and message.from_user.id == CONFIG.owner_id:
            return True


class IsOP(Filter):
    key = "is_op"

    def __init__(self, is_op):
        self.is_owner = is_op

    async def __call__(self, message: Message):
        if message.from_user and message.from_user.id in CONFIG.operators:
            return True
