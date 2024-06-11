# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.modules.media_dl.utils.cache import MediaCache
from korone.modules.media_dl.utils.instagram import (
    InstaData,
    Media,
    MediaType,
    NotFoundError,
    get_instagram_data,
    mediaid_to_code,
    url_to_binary_io,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/")
REEL_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")
STORIES_PATTERN = re.compile(r"(?:stories)/(?:[^/?#&]+/)?(?P<media_id>[0-9]+)")
POST_URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/.*?(?=\s|$)")


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
        insta: InstaData, media_cache: dict | None = None
    ) -> list[InputMediaPhoto | InputMediaVideo] | None:
        media_list = []
        if media_cache:
            media_list.extend(
                [InputMediaPhoto(media["file"]) for media in media_cache.get("photo", [])]
                + [
                    InputMediaVideo(
                        media=media["file"],
                        duration=media["duration"],
                        width=media["width"],
                        height=media["height"],
                        thumb=media["thumbnail"],
                    )
                    for media in media_cache.get("video", [])
                ]
            )
            return media_list

        for media in insta.medias:
            media_binary = await url_to_binary_io(media.url)
            if media.type_name in {MediaType.GRAPH_IMAGE, MediaType.STORY_IMAGE}:
                media_list.append(InputMediaPhoto(media_binary))
            elif media.type_name in {MediaType.GRAPH_VIDEO, MediaType.STORY_VIDEO}:
                media_list.append(InputMediaVideo(media_binary))

        return media_list

    @staticmethod
    async def reply_with_media(
        message: Message,
        media: Media,
        text: str,
        media_cache: dict | None,
        keyboard: InlineKeyboardBuilder | None,
    ) -> Message | None:
        if media_cache:
            if media_cache.get("photo"):
                media_file = media_cache["photo"][0].get("file", await url_to_binary_io(media.url))
            elif media_cache.get("video"):
                media_file = media_cache["video"][0].get("file", await url_to_binary_io(media.url))
        else:
            media_file = await url_to_binary_io(media.url)

        if media.type_name in {
            MediaType.GRAPH_IMAGE,
            MediaType.STORY_IMAGE,
            MediaType.STORY_VIDEO,
        }:
            return await message.reply_photo(
                photo=media_file,
                caption=text,
                reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
            )
        if media.type_name == MediaType.GRAPH_VIDEO:
            return await message.reply_video(
                video=media_file,
                caption=text,
                reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
            )
        return None

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
                insta = await get_instagram_data(post_id)
            except NotFoundError:
                await message.reply_text(_("Oops! Something went wrong while fetching the post."))
                return

            text, keyboard = self.create_caption_and_keyboard(insta, post_url)

            cache = MediaCache(post_id)
            cache_data = await cache.get()

            if len(insta.medias) == 1:
                media = insta.medias[0]
                try:
                    sent_message = await self.reply_with_media(
                        message, media, text, cache_data, keyboard
                    )
                except Exception as e:
                    await message.reply_text(_("Failed to send media: {error}").format(error=e))
                else:
                    cache_ttl = int(timedelta(weeks=1).total_seconds())
                    await cache.set(sent_message, cache_ttl) if sent_message else None
                return

            media_list = await self.create_media_list(insta, cache_data)
            if not media_list:
                return

            media_list[-1].caption = text
            if post_url:
                media_list[-1].caption += f"\n\n<a href='{post_url}'>{_("Open in Instagram")}</a>"

            try:
                sent_message = await message.reply_media_group(media_list)
            except Exception as e:
                await message.reply_text(_("Failed to send media: {error}").format(error=e))
            else:
                cache_ttl = int(timedelta(weeks=1).total_seconds())
                await cache.set(sent_message, cache_ttl) if sent_message else None
