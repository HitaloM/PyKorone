from typing import Iterable, Optional, Sequence, TypeVar

from aiogram.types import Message, ReplyKeyboardMarkup
from openai.types import ResponseFormatJSONSchema, ResponseFormatText
from openai.types.chat import ChatCompletionMessageParam
from stfu_tg import HList, Title
from stfu_tg.doc import Doc, Element, PreformattedHTML

from sophie_bot.modules.ai.fsm.pm import AI_GENERATED_TEXT
from sophie_bot.modules.ai.utils.llms import OLD_DEFAULT_MODEL, OldAIModels
from sophie_bot.modules.ai.utils.old_message_history import OldAIMessageHistory
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.services.ai import openai_client
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log

RESPONSE_TYPE = TypeVar("RESPONSE_TYPE")


async def ai_generate(
    messages: Iterable[ChatCompletionMessageParam],
    model: OldAIModels = OLD_DEFAULT_MODEL,
    json_schema: Optional[ResponseFormatJSONSchema] = None,
) -> str:
    chat_completion = await openai_client.chat.completions.create(  # type: ignore
        messages=messages,
        model=model,
        response_format=json_schema if json_schema else ResponseFormatText(type="text"),
    )

    log.debug("ai_generate", content=chat_completion.choices[0].message.content)

    return chat_completion.choices[0].message.content or _("No text from AI")


async def ai_generate_schema(
    messages: Iterable[ChatCompletionMessageParam],
    schema: type[RESPONSE_TYPE],
    model: OldAIModels = OLD_DEFAULT_MODEL,
) -> RESPONSE_TYPE:
    chat_completion = await openai_client.beta.chat.completions.parse(  # type: ignore
        messages=messages,
        model=model,
        response_format=schema,
    )

    log.debug("ai_generate_schema", content=chat_completion.choices[0].message.content)

    return chat_completion.choices[0].message.parsed  # type: ignore


async def ai_reply(
    message: Message,
    messages: OldAIMessageHistory,
    model: OldAIModels = OLD_DEFAULT_MODEL,
    markup: Optional[ReplyKeyboardMarkup] = None,
    header_items: Sequence[Element] = (),
    doc_items: Sequence[Element] = (),
) -> Message:
    response = await ai_generate(messages, model)
    response = PreformattedHTML(legacy_markdown_to_html(response))

    header = HList(
        Title(AI_GENERATED_TEXT), Title("4o+", bold=False) if model != OldAIModels.GPT_4O_MINI else None, *header_items
    )

    doc = Doc(header, *doc_items, response)

    return await message.reply(str(doc), disable_web_page_preview=True, reply_markup=markup)
