from aiogram.types import Message
from ass_tg.types import OptionalArg

from sophie_bot.args.users import SophieUserArg
from sophie_bot.utils.i18n import lazy_gettext as l_


async def optional_user(message: Message | None, _data: dict):
    if message and message.reply_to_message:
        return {}
    return {"user": OptionalArg(SophieUserArg(l_("User")))}
