from enum import Enum
from typing import Iterable, Optional

from aiogram.types import Message
from openai.types import ResponseFormatJSONSchema, ResponseFormatText
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from stfu_tg import Doc, HList, Title

from sophie_bot.modules.ai.fsm.pm import AI_GENERATED_TEXT
from sophie_bot.services.ai import ai_client

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


DEFAULT_MODEL = Models.GPT_4O_MINI


async def ai_response(
    messages: Iterable[ChatCompletionMessageParam],
    model: Models = DEFAULT_MODEL,
    json_schema: Optional[ResponseFormatJSONSchema] = None,
) -> str:
    chat_completion = await ai_client.chat.completions.create(  # type: ignore
        messages=messages,
        model=model,
        response_format=json_schema if json_schema else ResponseFormatText(type="text"),
    )

    return chat_completion.choices[0].message.content


def build_history(
    user_text: str,
    system_message: str = "",
    additional_history: Iterable[ChatCompletionMessageParam] = (),
    user_name: str = "Unknown",
) -> Iterable[ChatCompletionMessageParam]:
    return [
        ChatCompletionSystemMessageParam(content=AI_PROMPT + system_message, role="system"),
        *additional_history,
        ChatCompletionUserMessageParam(
            content=user_text,
            role="user",
            name=sanitize_name(user_name),
        ),
    ]


async def handle_ai_chatbot(
    message: Message,
    user_text: str,
    history: Iterable[ChatCompletionMessageParam],
    model: Models = DEFAULT_MODEL,
    system_message: str = "",
) -> Message:
    user_name = message.from_user.first_name if message.from_user else "Unknown"
    messages = build_history(user_text, system_message, history, user_name)

    response = await ai_response(messages, model)

    doc = Doc(
        HList(Title(AI_GENERATED_TEXT), Title("4o+", bold=False) if model != Models.GPT_4O_MINI else None),
        response,
    )

    return await message.reply(str(doc), disable_web_page_preview=True)
