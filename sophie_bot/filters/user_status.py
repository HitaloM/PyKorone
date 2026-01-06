from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import Message

from sophie_bot.config import CONFIG
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.utils.i18n import gettext as _


class IsAdmin(Filter):
    key = "is_admin"

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def __call__(self, event, *args, **kwargs):
        if hasattr(event, "message"):
            chat_id = event.message.chat.iid
        else:
            chat_id = event.chat.iid

        if not await is_user_admin(chat_id, event.from_user.iid):
            task = event.answer if hasattr(event, "message") else event.reply
            await task(_("Admin permission required!"))
            raise SkipHandler
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
