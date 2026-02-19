from __future__ import annotations

from asyncio import gather
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic_ai.messages import (
    BinaryContent,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from stfu_tg import HList, KeyValue, Section, VList

from korone.config import CONFIG
from korone.logger import get_logger
from korone.utils.i18n import gettext as _

from .cache_messages import get_cached_messages
from .self_reply import cut_titlebar, is_ai_message

if TYPE_CHECKING:
    from aiogram.types import Message
    from pydantic_ai.messages import UserContent
    from stfu_tg.doc import Element

    from .cache_messages import MessageType

logger = get_logger(__name__)


class AIUserMessageFormatter:
    @staticmethod
    def sanitize_name(name: str) -> str:
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        return "".join(char for char in name if char in allowed_chars) or "Unknown"

    @classmethod
    def user_message(cls, text: str, name: str, reply_to_user: str | None = None) -> str:
        name = cls.sanitize_name(name)
        if reply_to_user:
            reply_to_user = cls.sanitize_name(reply_to_user)
            return f"{name} (reply to {reply_to_user}): {text}"
        return f"{name}: {text}"


class NewAIMessageHistory:
    message_history: list[ModelRequest | ModelResponse]
    prompt: list[UserContent]

    def __init__(self) -> None:
        self.message_history = []
        self.prompt = []

    def add_chatbot_system_msg(self, additional: str = "") -> None:
        today = datetime.now(UTC).strftime("%d %B %Y, %H:%M")
        system_message = "\n".join((
            _("You're a telegram bot named Korone."),
            _("Be funny when the topic is casual."),
            _(
                "Do not use tables, use only the following markdown elements: "
                "** for bold, ~~ for strikethrough, ` for code, ``` for code blocks and []() for links."
            ),
            _("Send short messages unless longer explanations are needed."),
            _("Focus primarily on answering the latest user message."),
            _("Use the conversation history only for context, but respond specifically to the latest prompt."),
            _("Prefer to search information in the internet."),
            _("Today is ") + today,
            " ",
        ))
        self.message_history.append(ModelRequest(parts=[SystemPromptPart(content=system_message + additional)]))

    @staticmethod
    async def _cache_transform_msg(msg: MessageType) -> ModelResponse | ModelRequest:
        """Transform cached entries into pydantic_ai messages."""
        if msg.role == "assistant" or msg.user_id == CONFIG.bot_id:
            text = cut_titlebar(msg.text) if is_ai_message(msg.text) else msg.text
            return ModelResponse(parts=[TextPart(content=text)])

        return ModelRequest(parts=[UserPromptPart(content=AIUserMessageFormatter.user_message(msg.text, msg.name))])

    async def add_from_cache(self, chat_id: int) -> None:
        """Append cached chat messages to message history."""
        cached = await get_cached_messages(chat_id)
        self.message_history.extend(await gather(*[self._cache_transform_msg(msg) for msg in cached]))

    async def add_from_message(
        self,
        message: Message,
        custom_text: str | None = None,
        *,
        normalize_texts: bool = False,
        allow_reply_messages: bool = True,
        disable_name: bool = False,
    ) -> None:
        """
        Add message content as current prompt for the next model call.
        """

        replied_user_name: str | None = None
        if allow_reply_messages and message.reply_to_message and message.reply_to_message.from_user:
            replied_user_name = message.reply_to_message.from_user.full_name
            await self.add_from_message(message.reply_to_message, allow_reply_messages=False)

        if not message.from_user:
            return

        is_korone = message.from_user.id == CONFIG.bot_id
        message_text = custom_text or message.text or message.caption or _("<No text provided>")
        if normalize_texts:
            message_text = " ".join(message_text.split()) or _("<No text provided>")

        prompt: list[UserContent] = [*self.prompt]

        if is_korone and is_ai_message(message_text):
            message_text = cut_titlebar(message_text)

        prompt.append(
            message_text
            if disable_name
            else AIUserMessageFormatter.user_message(
                text=message_text, name=message.from_user.full_name, reply_to_user=replied_user_name
            )
        )

        # The current AI backend does not support media prompts, so keep media as text hints.
        if message.photo:
            prompt.append(_("[User sent a photo]"))
        if message.sticker:
            prompt.append(_("[User sent a sticker]"))
        if message.voice:
            prompt.append(_("[User sent a voice message]"))

        self.prompt = prompt

    async def initialize_chat_history(self, chat_id: int, additional_system_prompt: str = "") -> NewAIMessageHistory:
        self.add_chatbot_system_msg(additional=additional_system_prompt)
        await self.add_from_cache(chat_id)
        logger.debug(
            "MessageHistory initialized",
            chat_id=chat_id,
            history_size=len(self.message_history),
            prompt_size=len(self.prompt),
        )
        return self

    def add_system(self, content: str) -> None:
        self.message_history.append(ModelRequest(parts=[SystemPromptPart(content=content)]))

    def add_custom(self, content: str, name: str | None) -> None:
        user_content = AIUserMessageFormatter.user_message(content, name or "User")
        self.message_history.append(ModelRequest(parts=[UserPromptPart(content=user_content)]))

    @staticmethod
    async def chatbot(
        message: Message, custom_user_text: str | None = None, additional_system_prompt: str = ""
    ) -> NewAIMessageHistory:
        history = NewAIMessageHistory()
        await history.initialize_chat_history(message.chat.id, additional_system_prompt=additional_system_prompt)
        await history.add_from_message(message, custom_text=custom_user_text, allow_reply_messages=True)
        return history

    def history_debug(self) -> Element:
        items = VList(prefix="\n")

        for msg in self.message_history:
            kv_parts: list[Element] = []
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    kv_parts.append(KeyValue(part.tool_name, str(part.args)))
                elif isinstance(part, ToolReturnPart):
                    kv_parts.append(KeyValue(part.tool_name, str(part.content)))
                else:
                    kv_parts.append(KeyValue(part.part_kind, str(getattr(part, "content", part))))
            items.append(HList(*kv_parts))

        prompt_items: list[str] = []
        for item in self.prompt:
            if isinstance(item, str):
                prompt_items.append(item)
            elif isinstance(item, BinaryContent):
                prompt_items.append(item.kind)
            else:
                prompt_items.append(str(item))

        items += Section(HList(*prompt_items), title="Prompt")
        return items

    @property
    def to_moderation(self) -> list[dict[str, str]]:
        moderation_content: list[dict[str, str]] = []

        for msg in self.message_history:
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    moderation_content.append({"role": "system", "content": part.content})
                elif isinstance(part, TextPart):
                    moderation_content.append({"role": "assistant", "content": part.content})
                elif isinstance(part, UserPromptPart):
                    content_str = part.content if isinstance(part.content, str) else str(part.content)
                    moderation_content.append({"role": "user", "content": content_str})
                elif isinstance(part, BinaryContent):
                    continue

        moderation_content.extend(
            {"role": "user", "content": content} for content in self.prompt if isinstance(content, str)
        )

        return moderation_content
