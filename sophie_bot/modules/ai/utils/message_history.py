from asyncio import gather

from aiogram.types import Message
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionUserMessageParam,
)

from sophie_bot import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.utils.ai_chatbot import sanitize_name
from sophie_bot.modules.ai.utils.self_reply import cut_titlebar, is_ai_message


async def message_transform(msg):
    user = await ChatModel.get_by_chat_id(msg.user_id)

    first_name = user.first_name_or_title if user else "Unknown"

    return ChatCompletionUserMessageParam(role="user", content=msg.text, name=sanitize_name(first_name))


async def get_message_history(message: Message, data: dict):
    messages = await gather(*[message_transform(msg) for msg in data.get("cached_messages", [])])

    # Reply to the user
    if message.reply_to_message and message.reply_to_message.text and message.reply_to_message.from_user:

        replied_id = message.reply_to_message.from_user.id
        reply_text = message.reply_to_message.text

        if replied_id == CONFIG.bot_id:
            if is_ai_message(reply_text):
                reply_text = cut_titlebar(reply_text)

            messages.append(
                ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content="REPLIED MESSAGE:" + reply_text,
                    name="Sophie",
                )
            )
        else:
            messages.append(
                ChatCompletionUserMessageParam(
                    role="user",
                    content="REPLIED MESSAGE:" + message.reply_to_message.text,
                    name=sanitize_name(message.reply_to_message.from_user.first_name),
                )
            )

    return messages
