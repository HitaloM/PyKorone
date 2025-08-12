import datetime
from asyncio import gather
from typing import BinaryIO, Optional

from aiogram.types import Message
from attr import dataclass
from normality import normalize
from openai.types import ModerationMultiModalInputParam
from pydantic_ai.messages import (
    BinaryContent,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    UserContent,
    UserPromptPart,
)
from stfu_tg import HList, KeyValue, Section, VList
from stfu_tg.doc import Element

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.utils.cache_messages import (
    MessageType,
    get_cached_messages,
)
from sophie_bot.modules.ai.utils.self_reply import cut_titlebar, is_ai_message
from sophie_bot.modules.ai.utils.transform_audio import transform_voice_to_text
from sophie_bot.services.bot import bot
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


@dataclass
class ToCache:
    text: str
    chat_id: int
    user_id: int
    msg_id: int


class AIUserMessageFormatter:
    @staticmethod
    def sanitize_name(name: str) -> str:
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        return "".join(char for char in name if char in allowed_chars) or "Unknown"

    @classmethod
    def user_message(
        cls,
        text: str,
        name: str,
        reply_to_user: Optional[str] = None,
    ):
        name = cls.sanitize_name(name)
        if reply_to_user:
            reply_to_user = cls.sanitize_name(reply_to_user)
            text = f"From {name}, as reply to {reply_to_user}: {text}"

        return f"{name}: {text}"


class NewAIMessageHistory:
    """
    This class is used to store and construct the messages that are sent to the AI.
    """

    message_history: list[ModelRequest | ModelResponse]
    prompt: list[UserContent]

    def __init__(self):
        self.message_history = []
        self.prompt = []

    def add_chatbot_system_msg(self, additional: str = ""):
        today = datetime.datetime.now()
        system_message = "\n".join(
            (
                _("You're a telegram bot named Sophie."),
                _("Be funny when the topic is casual."),
                _(
                    "Do not use tables, use only the following markdown elements: ** for bold, ~~ for strikethrough, ` for code, ``` for code blocks and []() for links."
                ),
                _("Focus primarily on answering the LATEST user message."),
                _(
                    "Use the conversation history only for context, but respond specifically to the most recent question."
                ),
                _("Today is ") + today.strftime("%d %B %Y, %H:%M"),
                " ",
            )
        )
        self.message_history.append(ModelRequest(parts=[SystemPromptPart(content=system_message + additional)]))

    @staticmethod
    async def _cache_transform_msg(msg: MessageType) -> ModelResponse | ModelRequest:
        """Transforms a message from the cache to a message that can be sent to the AI."""
        user = await ChatModel.get_by_chat_id(msg.user_id)
        first_name = user.first_name_or_title if user else "Unknown"

        if msg.user_id == CONFIG.bot_id:
            # TODO: remove the line below
            text = cut_titlebar(msg.text) if is_ai_message(msg.text) else msg.text
            return ModelResponse(parts=[TextPart(content=text)])

        return ModelRequest(parts=[UserPromptPart(content=AIUserMessageFormatter.user_message(msg.text, first_name))])

    async def add_from_cache(self, chat_id: int):
        """Adds messages from the cache to the message history."""
        self.message_history.extend(
            await gather(*[self._cache_transform_msg(msg) for msg in await get_cached_messages(chat_id)])
        )

    async def add_from_message(
        self,
        message: Message,
        custom_text: Optional[str] = None,
        normalize_texts: bool = False,
        allow_reply_messages: bool = True,
        disable_name: bool = False,
    ):
        """Adds a user message to the context, returns a list of additional messages to cache for future use."""

        # Handle replied message first
        replied_user_name: str | None = None
        if allow_reply_messages and message.reply_to_message and message.reply_to_message.from_user:
            replied_user_name = message.reply_to_message.from_user.full_name
            await self.add_from_message(message.reply_to_message, allow_reply_messages=False)

        if not message.from_user:  # Linter insists on checking this
            return

        user_id = message.from_user.id
        is_sophie = user_id == CONFIG.bot_id

        message_text = custom_text or message.text or message.caption or _("<No text provided>")
        if normalize_texts:
            message_text = normalize(message_text) or _("<No text provided>")

        prompt: list[UserContent] = self.prompt or []

        # Cut the AI titlebar
        if is_sophie and is_ai_message(message_text):
            message_text = cut_titlebar(message_text)

        # Message's text
        prompt.append(
            message_text
            if disable_name
            else AIUserMessageFormatter.user_message(
                text=message_text,
                name=message.from_user.full_name,
                reply_to_user=replied_user_name,
            )
        )

        # Photos
        if message.photo:
            photo = message.photo[-1]
            downloaded_photo: Optional[BinaryIO] = await bot.download(photo)

            if not downloaded_photo:
                raise SophieException(_("Photo is empty"))

            prompt.append(
                BinaryContent(
                    media_type="image/jpeg",
                    data=downloaded_photo.read(),
                )
            )

        # Voice
        if message.voice:
            voice_text = await transform_voice_to_text(message.voice)
            prompt.append(voice_text)
            # TODO: Cache message somehow again?

        self.prompt = prompt

    async def initialize_chat_history(self, chat_id: int, additional_system_prompt: str = ""):
        # Add system message
        self.add_chatbot_system_msg(additional=additional_system_prompt)

        # Add messages from cache
        await self.add_from_cache(chat_id)

        log.debug("MessageHistory: message_history", history=self.message_history)
        return self

    def add_system(self, content: str):
        """Add a system message to the message history."""
        self.message_history.append(ModelRequest(parts=[SystemPromptPart(content=content)]))

    def add_custom(self, content: str, name: Optional[str]):
        """Add a custom user message to the message history."""
        user_content = AIUserMessageFormatter.user_message(content, name or "User")
        self.message_history.append(ModelRequest(parts=[UserPromptPart(content=user_content)]))

    @staticmethod
    async def chatbot(
        message: Message, custom_user_text: Optional[str] = None, additional_system_prompt: str = ""
    ) -> "NewAIMessageHistory":
        """A simple chat-bot case - static method for compatibility."""
        history = NewAIMessageHistory()
        await history.initialize_chat_history(message.chat.id, additional_system_prompt=additional_system_prompt)
        await history.add_from_message(message, custom_text=custom_user_text, allow_reply_messages=True)
        return history

    def history_debug(self) -> Element:
        """Builds a debug message for the message history."""
        items = VList(prefix="\n")

        for msg in self.message_history:
            kv_parts: list[Element] = []
            for part in msg.parts:
                if isinstance(part, ToolCallPart):
                    kv_parts.append(KeyValue(part.tool_name, part.args))
                else:
                    # not all parts have 'content' attribute; guard for mypy and runtime
                    content_value = part.content if hasattr(part, "content") else str(part)
                    kv_parts.append(KeyValue(part.part_kind, content_value))
            items.append(HList(*kv_parts))

        items += Section(
            HList(*(item.kind if not isinstance(item, str) else item for item in self.prompt)),
            title="Prompt",
        )

        return items

    @property
    def to_moderation(self) -> list[ModerationMultiModalInputParam]:
        """Extract content for OpenAI moderation from message history and prompt."""
        moderation_content = []

        # Extract content from message history
        for msg in self.message_history:
            if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if isinstance(part, (TextPart, UserPromptPart, SystemPromptPart)):
                        moderation_content.append(part.content)
                    elif isinstance(part, BinaryContent):
                        # For binary content, we'd need to handle it appropriately
                        # For now, skip as the old implementation also focused on text
                        pass

        # Extract content from current prompt
        if self.prompt:
            for content in self.prompt:
                if isinstance(content, str):
                    moderation_content.append(content)

        return moderation_content  # type: ignore
