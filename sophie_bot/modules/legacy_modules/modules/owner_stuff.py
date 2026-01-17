from aiogram import Router
from aiogram.types import Message

from sophie_bot.config import CONFIG
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec

router = Router(name="owner_stuff")
__exclude_public__ = True


@get_strings_dec("owner_stuff")
async def __user_info__(message: Message, user_id, strings):
    if user_id == CONFIG.owner_id:
        return strings["father"]
    elif user_id in CONFIG.operators:
        return strings["sudo_crown"]
