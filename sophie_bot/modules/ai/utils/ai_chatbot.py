from enum import Enum
from typing import Iterable

from aiogram.types import Message
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from stfu_tg import Doc, HList, Title, Url

from sophie_bot import CONFIG
from sophie_bot.modules.ai.fsm.pm import AI_GENERATED_TEXT
from sophie_bot.services.ai import ai_client
from sophie_bot.utils.i18n import gettext as _

AI_PROMPT = """
You're a Telegram Bot named Sophie.
Respond concisely, be friendly, stick to the current topic.
Do not use markdown or html. You can use emojis.
"""


def sanitize_name(name: str) -> str:
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    return "".join(char for char in name if char in allowed_chars) or "Unknown"


class Models(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


async def handle_message(
    message: Message, user_text: str, history: Iterable[ChatCompletionMessageParam], model=Models.GPT_4O_MINI
) -> Message:
    messages = [
        ChatCompletionSystemMessageParam(content=AI_PROMPT, role="system"),
        *history,
        ChatCompletionUserMessageParam(
            content=user_text,
            role="user",
            name=sanitize_name(message.from_user.first_name) if message.from_user else "Unknown",
        ),
    ]

    chat_completion = await ai_client.chat.completions.create(
        messages=messages,
        model=model,
    )

    doc = Doc(
        HList(
            Title(AI_GENERATED_TEXT),
            Title("4o-", bold=False) if model != Models.GPT_4O_MINI else None
        ),
        chat_completion.choices[0].message.content,
    )

    return await message.reply(str(doc), disable_web_page_preview=True)
