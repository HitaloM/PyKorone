from asyncio import gather
from base64 import b64encode
from itertools import chain
from typing import BinaryIO, Optional

from aiogram.types import Message
from attr import dataclass
from normality import normalize
from openai.types import ModerationMultiModalInputParam
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.utils.cache_messages import (
    MessageType,
    cache_message,
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


class AIMessageHistory(list[ChatCompletionMessageParam]):
    to_cache: list[ToCache] = []

    @staticmethod
    def _sanitize_name(name: str) -> str:
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        return "".join(char for char in name if char in allowed_chars) or "Unknown"

    async def _cache_transform_msg(
        self, msg: MessageType
    ) -> ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam:
        user = await ChatModel.get_by_chat_id(msg.user_id)
        first_name = user.first_name_or_title if user else "Unknown"

        if msg.user_id == CONFIG.bot_id:
            # TODO: remove the line below
            text = cut_titlebar(msg.text) if is_ai_message(msg.text) else msg.text
            return ChatCompletionAssistantMessageParam(role="assistant", content=text, name="Sophie")

        return ChatCompletionUserMessageParam(role="user", content=msg.text, name=self._sanitize_name(first_name))

    def add_chatbot_system_msg(self, additional: str = ""):
        system_message = "\n".join(
            (
                _("You're a bot named Sophie."),
                _("Respond concisely and stick to the current topic."),
                _(
                    "Please use only the following markdown elements: ** for bold, ~~ for strikethrough, ` for code, and ``` for preformatted text."
                ),
                _("Don't use Tables. You can use emojis."),
            )
        )
        self.append(ChatCompletionSystemMessageParam(content=system_message + additional, role="system"))

    async def add_from_cache(self, chat_id: int):
        self.extend(await gather(*[self._cache_transform_msg(msg) for msg in await get_cached_messages(chat_id)]))

    def add_system(self, content: str):
        self.append(ChatCompletionSystemMessageParam(content=content, role="system"))

    def add_custom(self, content: str, name: Optional[str]):
        self.append(ChatCompletionUserMessageParam(content=content, role="user", name=name or "User"))

    async def add_from_message(
        self,
        message: Message,
        reply_to_user: Optional[str] = None,
        custom_user_text: Optional[str] = None,
        normalize_texts: bool = False,
    ):
        """Adds a user message to the context, returns a list of additional messages to cache for future use."""

        if not message.from_user:
            return

        user_id = message.from_user.id
        user_name = self._sanitize_name(message.from_user.full_name)

        is_sophie = user_id == CONFIG.bot_id

        text = custom_user_text or message.text or message.caption or _("<No text provided>")
        if normalize_texts:
            text = normalize(text) or _("<No text provided>")

        content: list[ChatCompletionContentPartParam] = []

        # Cut the AI titlebar
        if is_sophie and is_ai_message(text):
            text = cut_titlebar(text)

        if reply_to_user:
            reply_prompt = _("REPLY TO").upper()
            text = f"<{reply_prompt} {reply_to_user}>: {text}"

        content.append(ChatCompletionContentPartTextParam(type="text", text=text))

        # Media
        if message.photo:
            photo = message.photo[-1]
            downloaded_photo: Optional[BinaryIO] = await bot.download(photo)

            if not downloaded_photo:
                raise SophieException(_("Photo is empty"))

            photo_base64 = b64encode(downloaded_photo.read())

            content.append(
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url=ImageURL(url=f"data:image/jpeg;base64,{photo_base64.decode()}", detail="auto"),
                )
            )

        # Voice
        if message.voice:
            voice_text = await transform_voice_to_text(message.voice)
            content.append(ChatCompletionContentPartTextParam(type="text", text=voice_text))
            self.to_cache.append(
                ToCache(
                    text=voice_text,
                    chat_id=message.chat.id,
                    user_id=user_id,
                    msg_id=message.message_id,
                )
            )

        self.append(
            {  # type: ignore
                "role": "assistant" if is_sophie else "user",
                "content": content,
                "name": user_name,
            }
        )

    async def cache(self):
        for msg_to_cache in self.to_cache:
            log.debug("MessageHistory: caching additional message", message=msg_to_cache)
            await cache_message(msg_to_cache.text, msg_to_cache.chat_id, msg_to_cache.user_id, msg_to_cache.msg_id)

    async def add_from_message_with_reply(self, message: Message, custom_user_text: Optional[str] = None):
        if message.reply_to_message and message.reply_to_message.from_user:
            await self.add_from_message(message.reply_to_message)
            reply_to_user = message.reply_to_message.from_user.full_name
        else:
            reply_to_user = None

        await self.add_from_message(message, reply_to_user=reply_to_user, custom_user_text=custom_user_text)

    @staticmethod  # TODO: Unstatic it
    async def chatbot(
        message: Message, custom_user_text: Optional[str] = None, additional_system_prompt: str = ""
    ) -> "AIMessageHistory":
        """A simple chat-bot case"""

        history = AIMessageHistory()
        history.add_chatbot_system_msg(additional=additional_system_prompt)
        await history.add_from_cache(message.chat.id)

        # Handle message reply
        await history.add_from_message_with_reply(message, custom_user_text=custom_user_text)

        # Cache additional messages
        await history.cache()

        log.debug("MessageHistory: chatbot", history=history)
        return history

    @property
    def to_moderation(self) -> list[ModerationMultiModalInputParam]:
        return list(chain(*(item["content"] for item in self)))  # type: ignore
