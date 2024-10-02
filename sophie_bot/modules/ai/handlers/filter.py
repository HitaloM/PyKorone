from contextlib import suppress

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from stfu_tg import Doc

from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.utils.ai_chatbot import handle_ai_chatbot
from sophie_bot.modules.ai.utils.message_history import get_message_history
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


async def ai_setup_start(message: Message):
    with suppress(TelegramBadRequest):
        await message.edit_text(
            str(
                Doc(
                    _("Please send me the AI instruction to proceed!"),
                    _("The AI will try to remember the chat context and will respond accordingly!"),
                    _(
                        "For example, you can combine it with the warn filter: 'Tell the user how bad it is to speak"
                        " profanity'"
                    ),
                )
            )
        )


async def ai_setup_finish(message: Message, _data: dict):
    if message.text is None:
        await message.reply(_("Should be AI prompt, please try again!"))
        return False
    return {"prompt": message.text}


async def ai_filter_handle(message: Message, chat: dict, data):
    prompt = data["prompt"]

    chat_db = await ChatModel.get_by_chat_id(chat["chat_id"])

    if not chat_db:
        raise SophieException("Chat not found in database")

    text = message.text or message.caption

    if text and await AIThrottleFilter().__call__(message, chat_db):
        history = await get_message_history(message)
        await handle_ai_chatbot(message, text, history, system_message=prompt)


def get_filter():
    return {
        "ai_text": {
            "title": l_("✨ AI Response"),
            "setup": {"start": ai_setup_start, "finish": ai_setup_finish},
            "handle": ai_filter_handle,
        }
    }
