from asyncio import gather
from base64 import b64encode
from typing import BinaryIO, Optional

from aiogram.types import Message
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

from sophie_bot import CONFIG, bot
from sophie_bot.db.models import ChatModel
from sophie_bot.modules.ai.utils.cache_messages import MessageType, get_cached_messages
from sophie_bot.modules.ai.utils.self_reply import cut_titlebar, is_ai_message
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


class MessageHistory(list[ChatCompletionMessageParam]):
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
            text = cut_titlebar(msg.text)
            return ChatCompletionAssistantMessageParam(role="assistant", content=text, name="Sophie")

        return ChatCompletionUserMessageParam(role="user", content=msg.text, name=self._sanitize_name(first_name))

    def add_system_msg(self, additional: str = ""):
        system_message = "\n".join(
            (
                _("You're a Telegram Bot named Sophie."),
                _("Respond concisely, be friendly, stick to the current topic."),
                _("Do not use markdown or html. You can use emojis."),
            )
        )
        self.append(ChatCompletionSystemMessageParam(content=system_message + additional, role="system"))

    async def add_from_cache(self, chat_id: int):
        self.extend(await gather(*[self._cache_transform_msg(msg) for msg in await get_cached_messages(chat_id)]))

    async def add_from_message(
        self,
        message: Message,
        reply_to_user: Optional[str] = None,
        custom_user_text: Optional[str] = None,
    ):
        if not message.from_user:
            return

        user_id = message.from_user.id
        user_name = self._sanitize_name(message.from_user.full_name)

        is_sophie = user_id == CONFIG.bot_id

        text = custom_user_text or message.text or message.caption or _("<No text provided>")

        content: list[ChatCompletionContentPartParam] = []

        # Cut the AI titlebar
        if is_sophie and is_ai_message(text):
            text = cut_titlebar(text)

        if reply_to_user:
            reply_prompt = _("MESSAGE REPLIES TO PREVIOUS MESSAGE FROM").upper()
            text = f"<{reply_prompt}: {reply_to_user}> {text}"

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

        self.append(
            {  # type: ignore
                "role": "assistant" if is_sophie else "user",
                "content": content,
                "name": user_name,
            }
        )

    @staticmethod
    async def chatbot(
        message: Message,
        custom_user_text: Optional[str] = None,
        additional_system_prompt: str = "",
    ) -> "MessageHistory":
        """A simple chat-bot case"""

        messages = MessageHistory()
        messages.add_system_msg(additional=additional_system_prompt)
        await messages.add_from_cache(message.chat.id)

        if message.reply_to_message and message.reply_to_message.from_user:
            await messages.add_from_message(message.reply_to_message)
            reply_to_user = message.reply_to_message.from_user.full_name
        else:
            reply_to_user = None

        await messages.add_from_message(message, reply_to_user=reply_to_user, custom_user_text=custom_user_text)

        log.debug("MessageHistory: chatbot", messages=messages)
        return messages
