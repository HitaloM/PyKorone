# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


import io

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.modules.media_dl.utils.instagram import (
    GRAPH_IMAGE,
    GRAPH_VIDEO,
    POST_URL_PATTERN,
    REEL_PATTERN,
    STORIES_PATTERN,
    STORY_IMAGE,
    STORY_VIDEO,
    URL_PATTERN,
    GetInstagram,
    InstaData,
    Media,
    NotFoundError,
    mediaid_to_code,
    url_to_binary_io,
)
from korone.utils.i18n import gettext as _


class InstagramHandler(MessageHandler):
    @staticmethod
    def get_post_id_from_message(message: Message) -> str | None:
        matches = REEL_PATTERN.findall(message.text)
        if matches:
            return matches[0]

        media_id_match = STORIES_PATTERN.findall(message.text)
        if media_id_match:
            try:
                return mediaid_to_code(int(media_id_match[0]))
            except ValueError:
                return None

        return None

    @staticmethod
    def create_caption_and_keyboard(
        insta: InstaData, post_url: str | None
    ) -> tuple[str, InlineKeyboardBuilder | None]:
        caption = f"<b>{insta.username}</b>"
        if insta.caption:
            caption += (
                f":\n\n{insta.caption[:255]}..."
                if len(insta.caption) > 255
                else f":\n\n{insta.caption}"
            )

        keyboard = InlineKeyboardBuilder() if post_url else None
        if post_url and keyboard:
            keyboard.button(text=_("Open in Instagram"), url=post_url)

        return caption, keyboard

    @staticmethod
    async def create_media_list(
        insta: InstaData,
    ) -> list[InputMediaPhoto | InputMediaVideo] | None:
        media_list = []
        for media in insta.medias:
            media_binary = await url_to_binary_io(media.url)
            if media.type_name in {GRAPH_IMAGE, STORY_IMAGE}:
                media_list.append(InputMediaPhoto(media_binary))
            elif media.type_name in {GRAPH_VIDEO, STORY_VIDEO}:
                media_list.append(InputMediaVideo(media_binary))

        return media_list

    @staticmethod
    async def reply_with_media(
        message: Message,
        media: Media,
        media_binary: io.BytesIO,
        text: str,
        keyboard: InlineKeyboardBuilder | None,
    ) -> None:
        if media.type_name in {GRAPH_IMAGE, STORY_IMAGE, STORY_VIDEO}:
            await message.reply_photo(
                media_binary,
                caption=text,
                reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
            )
        elif media.type_name == GRAPH_VIDEO:
            await message.reply_video(
                media_binary,
                caption=text,
                reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
            )

    @router.message(filters.regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        post_id = self.get_post_id_from_message(message)
        if not post_id:
            await message.reply_text(_("This Instagram URL is not a valid post or story."))
            return

        post_url_match = POST_URL_PATTERN.search(message.text)
        post_url = post_url_match.group() if post_url_match else None

        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            try:
                insta = await GetInstagram().get_data(post_id)
            except NotFoundError:
                await message.reply_text(_("Oops! Something went wrong while fetching the post."))
                return

            text, keyboard = self.create_caption_and_keyboard(insta, post_url)

            if len(insta.medias) == 1:
                media = insta.medias[0]
                media_binary = await url_to_binary_io(media.url)
                await self.reply_with_media(message, media, media_binary, text, keyboard)
                return

            media_list = await self.create_media_list(insta)
            if not media_list:
                return

            media_list[-1].caption = text
            if post_url:
                media_list[-1].caption += f"\n\n<a href='{post_url}'>{_("Open in Instagram")}</a>"

            await message.reply_media_group(media_list)
