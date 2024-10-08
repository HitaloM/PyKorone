from enum import Enum
from typing import Iterable, Optional, Sequence

from aiogram.types import Message, ReplyKeyboardMarkup
from openai.types import ResponseFormatJSONSchema, ResponseFormatText
from openai.types.chat import ChatCompletionMessageParam
from stfu_tg import HList, Title
from stfu_tg.doc import Doc, Element

from sophie_bot.modules.ai.fsm.pm import AI_GENERATED_TEXT
from sophie_bot.modules.ai.utils.message_history import MessageHistory
from sophie_bot.services.ai import ai_client


class Models(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


DEFAULT_MODEL = Models.GPT_4O_MINI


async def ai_generate(
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


async def ai_reply(
    message: Message,
    messages: MessageHistory,
    model: Models = DEFAULT_MODEL,
    markup: Optional[ReplyKeyboardMarkup] = None,
    header_items: Sequence[Element] = (),
    doc_items: Sequence[Element] = (),
) -> Message:
    response = await ai_generate(messages, model)

    header = HList(
        Title(AI_GENERATED_TEXT), Title("4o+", bold=False) if model != Models.GPT_4O_MINI else None, *header_items
    )

    doc = Doc(header, *doc_items, response)

    return await message.reply(str(doc), disable_web_page_preview=True, reply_markup=markup)
