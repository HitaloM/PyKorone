# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import pickle
import random
import re
import string
from datetime import timedelta
from pathlib import Path

import aiofiles
import orjson
from cashews.exceptions import CacheError
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message
from magic_filter import F

from korone import app_dir, cache
from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.media_dl.utils.twitter import (
    TweetData,
    TweetMedia,
    TweetMediaVariants,
    TwitterAPI,
    TwitterError,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")
DOWNLOADS_DIR = "downloads"
ORIGINAL_VIDEO_PREFIX = "tweet_original_video-"
CONVERTED_VIDEO_PREFIX = "tweet_converted_video-"


class FileUtils:
    @staticmethod
    def generate_random_file_path(prefix: str) -> Path:
        output_path = Path(app_dir / DOWNLOADS_DIR)
        output_path.mkdir(exist_ok=True, parents=True)

        random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        return output_path / f"{prefix}{random_suffix}.mp4"

    @staticmethod
    async def save_binary_io(binary_io) -> str:
        output_file_path = FileUtils.generate_random_file_path(ORIGINAL_VIDEO_PREFIX)

        try:
            async with aiofiles.open(output_file_path, "wb") as file:
                await file.write(binary_io.read())
        except OSError as e:
            msg = f"Failed to save binary IO: {e}"
            raise RuntimeError(msg) from e

        return output_file_path.as_posix()

    @staticmethod
    async def video_has_audio(video_path: str) -> bool:
        command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", video_path]

        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await process.communicate()
            output = orjson.loads(stdout)
        except (OSError, ValueError) as e:
            msg = f"Failed to check video audio: {e}"
            raise RuntimeError(msg) from e

        return any(stream["codec_type"] == "audio" for stream in output["streams"])

    @staticmethod
    async def add_silent_audio(video_path: str) -> str:
        output_file_path = FileUtils.generate_random_file_path(CONVERTED_VIDEO_PREFIX).as_posix()
        command = [
            "ffmpeg",
            "-i",
            video_path,
            "-f",
            "lavfi",
            "-i",
            "anullsrc",
            "-shortest",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            output_file_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
            )
            await process.communicate()
        except OSError as e:
            msg = f"Failed to add silent audio: {e}"
            raise RuntimeError(msg) from e

        return output_file_path

    @staticmethod
    async def delete_files(files: list[str]) -> None:
        loop = asyncio.get_event_loop()
        await asyncio.gather(
            *(
                loop.run_in_executor(None, lambda file: Path(file).unlink(missing_ok=True), file)
                for file in files
            )
        )


class CacheUtils:
    @staticmethod
    async def get_cache(key: str):
        try:
            cache_data = await cache.get(key)
            if cache_data:
                return pickle.loads(cache_data)
        except CacheError:
            pass
        return None

    @staticmethod
    async def set_cache(key: str, value: dict, expire: int):
        try:
            serialized_cache = pickle.dumps(value)
            await cache.set(key, serialized_cache, expire=expire)
        except CacheError:
            pass


class TwitterMediaHandler:
    __slots__ = ("api", "files_utils")

    def __init__(self):
        self.api = TwitterAPI()
        self.files_utils = FileUtils()

    @staticmethod
    async def get_best_variant(media: TweetMedia) -> TweetMediaVariants | None:
        if not media.variants:
            return None

        return max(media.variants, key=lambda variant: variant.bitrate)

    async def process_video_media(self, media: TweetMedia | TweetMediaVariants) -> str:
        original_file = await self.files_utils.save_binary_io(media.binary_io)
        has_audio = await self.files_utils.video_has_audio(original_file)

        if has_audio:
            return original_file

        converted_file = await self.files_utils.add_silent_audio(original_file)
        await self.files_utils.delete_files([original_file])

        return converted_file

    @staticmethod
    def serialize_media_dict(
        sent: list[Message],
    ) -> dict[str, dict[str, str | dict[str, str | int]]]:
        media_dict = {}

        for m in sent:
            if m.photo:
                media_dict[m.photo.file_id] = {"photo": m.photo.file_id}

            if m.video:
                thumbnail = m.video.thumbs[0].file_id if m.video.thumbs else None
                media_dict[m.video.file_id] = {
                    "video": {
                        "file": m.video.file_id,
                        "duration": m.video.duration,
                        "width": m.video.width,
                        "height": m.video.height,
                        "thumbnail": thumbnail,
                    }
                }

        return media_dict

    @staticmethod
    def create_media_list(media_cache: dict, text: str) -> list[InputMediaPhoto | InputMediaVideo]:
        media_list = [
            InputMediaPhoto(media["photo"])
            if "photo" in media
            else InputMediaVideo(
                media=media["video"]["file"],
                duration=media["video"]["duration"],
                width=media["video"]["width"],
                height=media["video"]["height"],
                thumb=media["video"]["thumbnail"],
            )
            for media in media_cache.values()
        ]
        media_list[-1].caption = text
        return media_list


class TwitterMessageHandler(MessageHandler):
    __slots__ = ("cache_utils", "media_handler")

    def __init__(self):
        self.media_handler = TwitterMediaHandler()
        self.cache_utils = CacheUtils()

    async def handle_multiple_media(self, message: Message, tweet: TweetData, text: str) -> None:
        cache_key = f"tweet:{tweet.url}:media"
        media_cache = await self.cache_utils.get_cache(cache_key)

        if media_cache:
            media_list = self.media_handler.create_media_list(media_cache, text)
            await message.reply_media_group(media=media_list)
            return

        media_tasks = []
        files_to_delete = []

        async def process_media(media):
            if media.type == "photo":
                return InputMediaPhoto(media.binary_io)
            if media.type in {"video", "gif"}:
                variant = await self.media_handler.get_best_variant(media) or media
                media_file = variant.binary_io

                try:
                    media_file = await self.media_handler.process_video_media(variant)
                    files_to_delete.append(media_file)
                except RuntimeError as e:
                    await message.reply_text(_("Failed to process video: {error}").format(error=e))
                    return None

                thumbnail_io = await self.media_handler.api._url_to_binary_io(media.thumbnail_url)
                return InputMediaVideo(
                    media=media_file,
                    duration=int(timedelta(milliseconds=media.duration).total_seconds()),
                    width=media.width,
                    height=media.height,
                    thumb=thumbnail_io,
                )
            return None

        media_tasks = [process_media(media) for media in tweet.media]

        media_list = await asyncio.gather(*media_tasks)
        media_list = [media for media in media_list if media]

        media_list[-1].caption = text
        sent = await message.reply_media_group(media=media_list)

        if files_to_delete:
            await self.media_handler.files_utils.delete_files(files_to_delete)

        media_dict = self.media_handler.serialize_media_dict(sent)
        await self.cache_utils.set_cache(
            cache_key, media_dict, expire=int(timedelta(weeks=1).total_seconds())
        )

    async def send_media(  # noqa: PLR0917
        self,
        client: Client,
        message: Message,
        media,
        text: str,
        tweet: TweetData,
        cache_data: dict | None,
    ) -> Message | None:
        keyboard = InlineKeyboardBuilder().button(text=_("Open in Twitter"), url=tweet.url)
        media_file = media.binary_io

        try:
            if media.type == "photo":
                if cache_data:
                    media_file = cache_data["photo"]["file"]

                return await client.send_photo(
                    chat_id=message.chat.id,
                    photo=media_file,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    reply_to_message_id=message.id,
                )
            if media.type in {"video", "gif"}:
                if not cache_data:
                    thumbnail_io = await self.media_handler.api._url_to_binary_io(
                        media.thumbnail_url
                    )
                    media_file = (
                        await self.media_handler.get_best_variant(media) or media
                    ).binary_io
                else:
                    media_file = cache_data["video"]["file"]

                if not media_file:
                    await message.reply_text(_("Failed to send media!"))
                    return None

                return await client.send_video(
                    chat_id=message.chat.id,
                    video=media_file,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    duration=cache_data.get("duration", 0)
                    if cache_data
                    else int(timedelta(milliseconds=media.duration).total_seconds()),
                    width=cache_data.get("width", 0) if cache_data else media.width,
                    height=cache_data.get("height", 0) if cache_data else media.height,
                    thumb=cache_data.get("thumbnail") if cache_data else thumbnail_io,
                    reply_to_message_id=message.id,
                )
        except Exception as e:
            await message.reply_text(_("Failed to send media: {error}").format(error=e))
        return None

    @staticmethod
    def format_tweet_text(tweet: TweetData) -> str:
        text = f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>):</b>\n\n"
        if tweet.text:
            text += f"{tweet.text[:900]}{"..." if len(tweet.text) > 900 else ""}"

        if tweet.source:
            text += _("\n\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)
        return text

    @staticmethod
    async def fetch_tweet_data(url: str) -> TweetData | None:
        api = TwitterAPI()

        try:
            await api.fetch(url)
            return api.tweet
        except TwitterError:
            return None

    @router.message(F.text.regexp(URL_PATTERN, search=True))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        tweet = await self.fetch_tweet_data(url_match.group())
        if not tweet:
            await message.reply_text(
                _(
                    "Failed to scan your link! This may be due to an incorrect link, "
                    "private/suspended account, deleted tweet, or recent changes to "
                    "Twitter's API."
                )
            )
            return

        if not tweet.media:
            await message.reply_text(_("No media found in this tweet!"))
            return

        text = self.format_tweet_text(tweet)
        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            if len(tweet.media) > 1:
                text += f"\n<a href='{tweet.url}'>Open in Twitter</a>"
                await self.handle_multiple_media(message, tweet, text)
                return

            cache_key = f"tweet:{tweet.url}:media"
            cache_data = await self.cache_utils.get_cache(cache_key)
            sent = await self.send_media(client, message, tweet.media[0], text, tweet, cache_data)

        if sent:
            media_dict = {}
            if sent.photo:
                media_dict = {
                    "photo": {"file": sent.photo.file_id},
                }
            elif sent.video:
                thumbnail = sent.video.thumbs[0].file_id if sent.video.thumbs else None
                media_dict = {
                    "video": {
                        "file": sent.video.file_id,
                        "duration": sent.video.duration,
                        "width": sent.video.width,
                        "height": sent.video.height,
                        "thumbnail": thumbnail,
                    }
                }

            await self.cache_utils.set_cache(
                cache_key, media_dict, expire=int(timedelta(weeks=1).total_seconds())
            )
