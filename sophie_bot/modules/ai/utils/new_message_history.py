from asyncio import gather
from typing import BinaryIO, Optional

from aiogram.types import Message
from attr import dataclass
from normality import normalize
from pydantic_ai.messages import ModelRequest, UserPromptPart, BinaryContent, \
    ImageMediaType, UserContent, SystemPromptPart, ModelRequestPart, ModelResponse, TextPart

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
            text = f"<From {name}, as reply to {reply_to_user}>:\n{text}"

        return f'<From {name}>:\n{text}'


class NewAIMessageHistory(list[ModelRequest | ModelResponse]):

    async def _cache_transform_msg(
            self, msg: MessageType
    ) -> ModelRequestPart:
        user = await ChatModel.get_by_chat_id(msg.user_id)
        first_name = user.first_name_or_title if user else "Unknown"

        if msg.user_id == CONFIG.bot_id:
            # TODO: remove the line below
            text = cut_titlebar(msg.text) if is_ai_message(msg.text) else msg.text
            return TextPart(content=text)

        return ModelRequest(parts=[UserPromptPart(content=AIUserMessageFormatter.user_message(msg.text, first_name))])

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
        self.append(ModelRequest(parts=[SystemPromptPart(content=system_message + additional)]))

    async def add_from_cache(self, chat_id: int):
        self.extend(await gather(*[self._cache_transform_msg(msg) for msg in await get_cached_messages(chat_id)]))

    def add_system(self, content: str):
        self.append(ModelRequest(parts=[SystemPromptPart(content=content)]))

    def add_custom(self, content: str, name: str):
        self.append(ModelRequest(parts=[UserPromptPart(
            content=AIUserMessageFormatter.user_message(content, name),
        )]))

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
        is_sophie = user_id == CONFIG.bot_id

        text = custom_user_text or message.text or message.caption or _("<No text provided>")
        if normalize_texts:
            text = normalize(text) or _("<No text provided>")

        content: list[UserContent] = []

        # Cut the AI titlebar
        if is_sophie and is_ai_message(text):
            text = cut_titlebar(text)

        # Message's text
        content.append(AIUserMessageFormatter.user_message(
            text=text,
            name=message.from_user.full_name,
            reply_to_user=reply_to_user,
        ))

        # Photos
        if message.photo:
            photo = message.photo[-1]  # last is the highest quality
            downloaded_photo: Optional[BinaryIO] = await bot.download(photo)

            if not downloaded_photo:
                raise SophieException(_("Photo is empty"))

            content.append(
                BinaryContent(
                    media_type=ImageMediaType,
                    data=downloaded_photo,
                )
            )

        # Voice
        if message.voice:
            voice_text = await transform_voice_to_text(message.voice)
            content.append(voice_text)
            # self.to_cache.append(
            #     ToCache(
            #         text=voice_text,
            #         chat_id=message.chat.id,
            #         user_id=user_id,
            #         msg_id=message.message_id,
            #     )
            # )

        self.append(ModelRequest(parts=[UserPromptPart(
            content=content,
            timestamp=message.date
        )]))

    # async def add_from_message_with_reply(self, message: Message, custom_user_text: Optional[str] = None):
    #     if message.reply_to_message and message.reply_to_message.from_user:
    #         await self.add_from_message(message.reply_to_message)
    #         reply_to_user = message.reply_to_message.from_user.full_name
    #     else:
    #         reply_to_user = None
    #
    #     await self.add_from_message(message, reply_to_user=reply_to_user, custom_user_text=custom_user_text)

    @staticmethod
    async def chatbot_history(chat_id: int, additional_system_prompt: str = ""):
        history = NewAIMessageHistory()
        history.add_chatbot_system_msg(additional=additional_system_prompt)
        await history.add_from_cache(chat_id)

        log.debug("MessageHistory: chatbot", history=history)
        return history
