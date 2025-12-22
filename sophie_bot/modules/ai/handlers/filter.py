from contextlib import suppress

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from stfu_tg import Doc

from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.filters.throttle import AIThrottleFilter
from sophie_bot.modules.ai.utils.ai_chatbot_reply import ai_chatbot_reply
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
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


async def ai_filter_handle(message: Message, chat: dict, data: dict):
    prompt = data["prompt"]

    chat_db = await ChatModel.get_by_tid(chat["chat_id"])

    if not chat_db:
        raise SophieException("Chat not found in database")

    if message.text or message.caption and await AIThrottleFilter().__call__(message, chat_db):
        from sophie_bot.middlewares.connections import ChatConnection

        connection = ChatConnection(
            type=chat_db.type,
            is_connected=False,
            id=chat_db.chat_id,
            title=chat_db.first_name_or_title,
            db_model=chat_db,
        )

        # Create history with custom system prompt
        history = NewAIMessageHistory()
        await history.initialize_chat_history(message.chat.id, additional_system_prompt=prompt)
        await history.add_from_message(message)

        await ai_chatbot_reply(message, connection, user_text=None)


def get_filter():
    return {
        "ai_text": {
            "title": l_("✨ AI Response"),
            "setup": {"start": ai_setup_start, "finish": ai_setup_finish},
            "handle": ai_filter_handle,
        }
    }
