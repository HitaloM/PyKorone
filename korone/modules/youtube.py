# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import datetime
import io
import re
import shutil
import tempfile
from contextlib import suppress
from pathlib import Path

import httpx
from pyrogram import filters
from pyrogram.enums import ChatAction
from pyrogram.errors import BadRequest, MessageDeleteForbidden, MessageNotModified
from pyrogram.helpers import ikb
from pyrogram.types import CallbackQuery, Message
from yt_dlp import DownloadError, YoutubeDL

from ..bot import Korone
from ..utils.aioify import run_async
from ..utils.convert import pretty_size
from ..utils.disable import disableable_dec
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args
from ..utils.youtube import (
    PLAYLIST_REGEX,
    TIME_REGEX,
    TWITTER_REGEX,
    YOUTUBE_REGEX,
    extract_info,
)


@Korone.on_message(filters.cmd("ytdl"))
@disableable_dec("ytdl")
@get_strings_dec("youtube")
async def ytdl_command(bot: Korone, message: Message, strings):
    args = get_args(message)
    user = message.from_user.id

    if message.text and args:
        url = args
    elif message.reply_to_message and message.reply_to_message.text:
        url = message.reply_to_message.text
    else:
        await message.reply_text(strings["no_url_ytdl"])
        return

    ydl = YoutubeDL(
        {
            "outtmpl": "dls/%(title)s-%(id)s.%(ext)s",
            "format": "mp4",
            "noplaylist": True,
        }
    )
    match = YOUTUBE_REGEX.match(url)
    playlist = PLAYLIST_REGEX.match(url)

    if playlist:
        await message.reply_text(strings["playlist_not_supported"])
        return

    t = TIME_REGEX.search(url)
    temp = t.group(1) if t else 0
    if match:
        yt = await run_async(extract_info, ydl, match.group(), download=False)
    else:
        yt = await run_async(extract_info, ydl, "ytsearch:" + url, download=False)
        if yt.get("entries") is not None and len(yt["entries"]) > 0:
            yt = yt["entries"][0]
        else:
            await message.reply_text(strings["not_found"])
            return

    for f in yt["formats"]:
        if f["format_id"] == "140" and f.get("filesize") is not None:
            afsize = f["filesize"] or 0
        if f["ext"] == "mp4" and f.get("filesize") is not None:
            vfsize = f["filesize"] or 0
            vformat = f["format_id"]

    keyboard = ikb(
        [
            [
                (
                    strings["audio"],
                    f"_aud.{yt['id']}|{afsize}|{vformat}|{temp}|{user}|{message.id}",
                ),
                (
                    strings["video"],
                    f"_vid.{yt['id']}|{vfsize}|{vformat}|{temp}|{user}|{message.id}",
                ),
            ]
        ]
    )

    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        performer = yt.get("creator") or yt.get("uploader")
        title = yt["title"]

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n"
    text += f"💾 <code>{pretty_size(afsize)}</code> (áudio) / \
<code>{pretty_size(int(vfsize))}</code> (vídeo)\n"
    text += f"⏳ <code>{datetime.timedelta(seconds=yt.get('duration'))}</code>"

    await message.reply_text(text, reply_markup=keyboard)


@Korone.on_callback_query(filters.regex(r"^(_(vid|aud))"))
@get_strings_dec("youtube")
async def ytdl_menu(bot: Korone, query: CallbackQuery, strings):
    message = query.message
    chat_id = message.chat.id

    data, fsize, vformat, temp, userid, mid = query.data.split("|")
    if query.from_user.id != int(userid):
        await query.answer(strings["not_for_you"], cache_time=60)
        return

    if int(fsize) > 2147483648:
        await query.answer(
            strings["download_limit"],
            show_alert=True,
            cache_time=60,
        )
        return

    vid = re.sub(r"^\_(vid|aud)\.", "", data)
    url = "https://www.youtube.com/watch?v=" + vid
    try:
        await message.edit(strings["downloading"])
    except MessageNotModified:
        await message.reply_text(strings["downloading"])

    await query.answer(strings["doing"], cache_time=0)
    with tempfile.TemporaryDirectory() as tempdir:
        path = Path(tempdir) / "ytdl"

    if "vid" in data:
        ydl = YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": f"{vformat}+140",
                "noplaylist": True,
            }
        )
    else:
        ydl = YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": "140",
                "extractaudio": True,
                "noplaylist": True,
            }
        )

    try:
        yt = await run_async(extract_info, ydl, url, download=True)
    except DownloadError as e:
        await message.edit(strings["error"].format(error=e))
        return

    await message.edit(strings["uploading"])
    filename = ydl.prepare_filename(yt)
    ttemp = f"⏰ {datetime.timedelta(seconds=int(temp))} | " if int(temp) else ""
    async with httpx.AsyncClient(http2=True) as client:
        thumb = io.BytesIO((await client.get(yt["thumbnail"])).content)
        thumb.name = "thumbnail.jpeg"

    caption = f"{ttemp} <a href='{yt['webpage_url']}'>{yt['title']}</a></b>"
    if yt.get("view_count"):
        caption += "\n<b>Views:</b> <code>{:,}</code>".format(yt["view_count"])
    if yt.get("like_count"):
        caption += "\n<b>Likes:</b> <code>{:,}</code>".format(yt["like_count"])

    try:
        if "vid" in data:
            await bot.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO)
            await bot.send_video(
                chat_id=chat_id,
                video=filename,
                width=1920,
                height=1080,
                caption=caption,
                duration=yt["duration"],
                thumb=thumb,
                reply_to_message_id=int(mid),
            )
        else:
            if " - " in yt["title"]:
                performer, title = yt["title"].rsplit(" - ", 1)
            else:
                performer = yt.get("creator") or yt.get("uploader")
                title = yt["title"]
            await bot.send_chat_action(chat_id, ChatAction.UPLOAD_AUDIO)
            await bot.send_audio(
                chat_id=chat_id,
                audio=filename,
                caption=caption,
                title=title,
                performer=performer,
                duration=yt["duration"],
                thumb=thumb,
                reply_to_message_id=int(mid),
            )
    except BadRequest as e:
        await message.edit_text(strings["error"].format(error=e))
    else:
        with suppress(MessageDeleteForbidden):
            await message.delete()

    shutil.rmtree(tempdir, ignore_errors=True)


@Korone.on_message(filters.cmd("ttdl"))
@disableable_dec("ttdl")
@get_strings_dec("youtube")
async def on_ttdl(bot: Korone, message: Message, strings):
    args = get_args(message)

    if message.text and args:
        url = args
    elif message.reply_to_message and message.reply_to_message.text:
        url = message.reply_to_message.text
    else:
        await message.reply_text(strings["no_url_ttdl"])
        return

    match = TWITTER_REGEX.match(url)
    if not match:
        await message.reply_text(strings["invalid_url"])
        return

    sent = await message.reply_text(strings["downloading"])

    with tempfile.TemporaryDirectory() as tempdir:
        path = Path(tempdir) / "ttdl"

    tdl = YoutubeDL(
        {
            "outtmpl": f"{path}/{message.from_user.id}-%(id)s.%(ext)s",
            "format": "mp4",
        }
    )
    tt = await run_async(extract_info, tdl, match.group(), download=False)

    for f in tt["formats"]:
        if f["ext"] == "mp4":
            vformat = f["format_id"]
            vheaders = f["http_headers"]

    tdl = YoutubeDL(
        {
            "outtmpl": f"{path}/{message.from_user.id}-%(id)s.%(ext)s",
            "format": vformat,
        }
    )

    try:
        tt = await run_async(extract_info, tdl, url, download=True)
    except BaseException as e:
        await sent.edit(strings["error"].format(error=e))
        return

    filename = tdl.prepare_filename(tt)
    async with httpx.AsyncClient(http2=True) as client:
        thumb = io.BytesIO((await client.get(tt["thumbnail"], headers=vheaders)).content)
        thumb.name = "thumbnail.jpeg"

    await sent.edit(strings["uploading"])
    keyboard = ikb([[("🔗 Tweet", tt["webpage_url"], "url")]])
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
    try:
        if "duration" in tt:
            await message.reply_video(
                video=filename,
                thumb=thumb,
                duration=int(tt["duration"]),
                reply_markup=keyboard,
            )
        else:
            await message.reply_video(
                video=filename,
                thumb=thumb,
                reply_markup=keyboard,
            )
    except BadRequest as e:
        await message.reply_text(strings["error"].format(error=e))
    else:
        await sent.delete()

    shutil.rmtree(tempdir, ignore_errors=True)


__help__ = True
