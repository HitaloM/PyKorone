from aiogram.types import CallbackQuery, InaccessibleMessage, Message
from stfu_tg.doc import Element

from korone.utils.exception import KoroneException
from korone.utils.i18n import gettext as _


async def reply_or_edit(event: Message | CallbackQuery, text: Element | str, **kwargs):
    if isinstance(event, CallbackQuery) and event.message:
        if isinstance(event.message, InaccessibleMessage):
            raise KoroneException(_("The message is inaccessible. Please write the command again"))

        return await event.message.edit_text(str(text), **kwargs)
    elif isinstance(event, Message):
        return await event.reply(str(text), **kwargs)
    else:
        raise ValueError("answer: Wrong event type")
