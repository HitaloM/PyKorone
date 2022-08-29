# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import asyncio
import datetime
import io
import os
import platform
import shutil
import signal
import sys
import traceback
from typing import Dict

import humanize
import psutil
import pyrogram
from kantex.html import Bold, Code, KanTeXDocument, KeyValueItem, Section
from meval import meval
from pyrogram import filters
from pyrogram.errors import BadRequest, FloodWait
from pyrogram.helpers import ikb
from pyrogram.types import (
    Animation,
    CallbackQuery,
    Document,
    Message,
    Photo,
    Sticker,
    Video,
)

from ..bot import Korone
from ..database import database
from ..database.chats import filter_chats_by_language
from ..database.users import filter_users_by_language
from ..utils.languages import LANGUAGES
from ..utils.messages import get_args
from ..utils.modules import ALL_MODULES
from ..utils.system import shell_exec

# for stats command
conn = database.get_conn()


@Korone.on_message(filters.cmd("ping") & filters.sudo)
async def ping(bot: Korone, message: Message):
    first = datetime.datetime.now()
    sent = await message.reply_text("<b>Pong!</b>")
    second = datetime.datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Korone.on_message(filters.cmd("loadedmodules") & filters.sudo)
async def loaded_modules(bot: Korone, message: Message):
    text = "".join(f"* {module}\n" for module in ALL_MODULES)
    await message.reply_text(text)


@Korone.on_message(filters.cmd("sh") & filters.sudo)
async def on_terminal_m(bot: Korone, message: Message):
    code = get_args(message)
    sm = await message.reply_text("Running...")

    stdout = await shell_exec(code)

    output = "".join(f"<code>{line}</code>\n" for line in stdout)
    output_message = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"
    if len(output) > 0:
        if len(output) > (4096 - len(output_message)):
            document = io.BytesIO(
                (output.replace("<code>", "").replace("</code>", "")).encode()
            )
            document.name = "output.txt"
            await bot.send_document(
                chat_id=message.chat.id,
                document=document,
                reply_to_message_id=message.id,
            )
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@Korone.on_message(filters.cmd("ev") & filters.sudo)
async def on_eval_m(bot: Korone, message: Message):
    eval_code = get_args(message)
    sm = await message.reply_text("Running...")
    try:
        stdout = await meval(eval_code, globals(), **locals())
    except BaseException:
        error = traceback.format_exc()
        await sm.edit_text(
            f"An error occurred while running the code:\n<code>{error}</code>"
        )
        return
    lines = str(stdout).split("\n")
    output = "".join(f"<code>{line}</code>\n" for line in lines)
    output_message = f"<b>Input\n&gt;</b> <code>{eval_code}</code>\n\n"
    if len(output) > 0:
        if len(output) > (4096 - len(output_message)):
            document = io.BytesIO(
                (output.replace("<code>", "").replace("</code>", "")).encode()
            )
            document.name = "output.txt"
            await bot.send_document(
                chat_id=message.chat.id,
                document=document,
                reply_to_message_id=message.id,
            )
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@Korone.on_message(filters.cmd("ex") & filters.sudo)
async def on_execute_m(bot: Korone, message: Message):
    code = get_args(message)
    sm = await message.reply_text("Running...")
    function = """
async def _aexec_(bot: Korone, message: Message):
    """
    for line in code.split("\n"):
        function += f"\n    {line}"
    exec(function)
    try:
        await locals()["_aexec_"](bot, message)
    except BaseException:
        error = traceback.format_exc()
        await sm.edit_text(
            f"An error occurred while running the code:\n<code>{error}</code>"
        )
        return
    output_message = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"
    await sm.edit_text(output_message)


@Korone.on_message(filters.cmd("reboot") & filters.sudo)
async def restart(bot: Korone, message: Message):
    await message.reply_text("Restarting...")
    args = [sys.executable, "-m", "korone"]
    os.execv(sys.executable, args)


def parse_commits(log: str) -> Dict:
    commits: Dict = {}
    last_commit = ""
    lines = log.split("\n")
    for line in lines:
        if line.startswith("commit"):
            last_commit = line.split()[1]
            commits[last_commit] = {}
        if len(line) > 0:
            if line.startswith("    "):
                if "title" in commits[last_commit].keys():
                    commits[last_commit]["message"] = line[4:]
                else:
                    commits[last_commit]["title"] = line[4:]
            elif ":" in line:
                key, value = line.split(": ")
                commits[last_commit][key] = value
    return commits


@Korone.on_message(filters.cmd("upgrade") & filters.sudo)
async def upgrade(c: Korone, m: Message):
    sm = await m.reply_text("Verificando...")

    await shell_exec("git fetch origin")
    stdout, proc = await shell_exec("git log HEAD..origin/main")

    if proc.returncode == 0:
        if len(stdout) <= 0:
            return await sm.edit_text("There is nothing to update.")
        changelog = "<b>Changelog</b>:\n"
        commits = parse_commits(stdout)
        for commit_hash, commit in commits.items():
            changelog += f"  - [<code>{commit_hash[:7]}</code>] {commit['title']}\n"
        changelog += f"\n<b>New commits count</b>: <code>{len(commits)}</code>."
        keyboard = ikb([[("🆕 Upgrade", "upgrade")]])
        await sm.edit_text(changelog, reply_markup=keyboard)
    else:
        lines = stdout.split("\n")
        error = "".join(f"<code>{line}</code>\n" for line in lines)
        await sm.edit_text(
            f"Update failed (process exited with {proc.returncode}):\n{error}"
        )


@Korone.on_callback_query(filters.regex(r"^upgrade$") & filters.sudo)
async def upgrade_cb(bot: Korone, callback: CallbackQuery):
    await callback.edit_message_reply_markup({})
    sent = await callback.message.reply_text("Upgrading...")

    stdout, proc = await shell_exec("git reset --hard origin/main")

    if proc.returncode == 0:
        await sent.edit_text("Restarting...")
        args = [sys.executable, "-m", "korone"]
        os.execv(sys.executable, args)
    else:
        lines = stdout.split("\n")
        error = "".join(f"<code>{line}</code>\n" for line in lines)
        await sent.edit_text(
            f"Update failed (process exited with {proc.returncode}):\n{error}"
        )


@Korone.on_message(filters.cmd("shutdown") & filters.sudo)
async def shutdown(bot: Korone, message: Message):
    await message.reply_text("Adeus...")
    os.kill(os.getpid(), signal.SIGINT)


@Korone.on_message(filters.cmd("echo") & filters.sudo)
async def echo(bot: Korone, message: Message):
    text = get_args(message)
    kwargs = {}
    reply = message.reply_to_message
    if reply:
        kwargs["reply_to_message_id"] = reply.id
    try:
        await message.delete()
    except BadRequest:
        pass
    await bot.send_message(chat_id=message.chat.id, text=text, **kwargs)


@Korone.on_message(filters.cmd("sysinfo") & filters.sudo)
async def bot_sysinfo(bot: Korone, message: Message):
    uname = platform.uname()

    # RAM usage
    vm = psutil.virtual_memory()
    vm_used = humanize.naturalsize(vm.used, binary=True)
    vm_total = humanize.naturalsize(vm.total, binary=True)

    # Swap usage
    sm = psutil.swap_memory()
    sm_used = humanize.naturalsize(sm.used, binary=True)
    sm_total = humanize.naturalsize(sm.total, binary=True)

    # CPU
    cpu_freq = psutil.cpu_freq().current
    if cpu_freq >= 1000:
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz"
    else:
        cpu_freq = f"{round(cpu_freq, 2)}MHz"
    cpu_usage = (
        f"{psutil.cpu_percent(interval=1)}% " f"({psutil.cpu_count()}) " f"{cpu_freq}"
    )

    # Uptime
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    date = now - bot.start_datetime

    doc = KanTeXDocument(
        Section(
            "Korone System Info",
            KeyValueItem(Bold("OS"), Code(uname.system)),
            KeyValueItem(Bold("Node"), Code(uname.node)),
            KeyValueItem(Bold("Kernel"), Code(uname.release)),
            KeyValueItem(Bold("Arch"), Code(uname.machine)),
            KeyValueItem(Bold("CPU"), Code(cpu_usage)),
            KeyValueItem(Bold("RAM"), Code(f"{vm_used}/{vm_total}")),
            KeyValueItem(Bold("Swap"), Code(f"{sm_used}/{sm_total}")),
            KeyValueItem(Bold("Uptime"), Code(humanize.precisedelta(date))),
        ),
        Section(
            "Python Libraries",
            KeyValueItem(Bold("Python"), Code(platform.python_version())),
            KeyValueItem(Bold("Pyrogram"), Code(pyrogram.__version__)),
        ),
    )

    await message.reply_text(doc, disable_web_page_preview=True)


@Korone.on_message(filters.cmd("stats") & filters.sudo)
async def stats(bot: Korone, message: Message):
    users_count = await conn.execute("select count() from users")
    users_count = await users_count.fetchone()

    groups_count = await conn.execute("select count() from chats")
    groups_count = await groups_count.fetchone()

    disk = shutil.disk_usage("/")

    doc = KanTeXDocument(
        Section(
            "Korone Database",
            KeyValueItem(
                Bold("Size"),
                Code(
                    humanize.naturalsize(
                        os.stat("./korone/database/db.sqlite").st_size, binary=True
                    )
                ),
            ),
            KeyValueItem(
                Bold("Free"), Code(humanize.naturalsize(disk[2], binary=True))
            ),
        ),
    )

    users_sec = Section("Korone Users", KeyValueItem(Bold("All"), Code(users_count[0])))
    for lang in LANGUAGES.values():
        language = lang["language_info"]
        users = await filter_users_by_language(language=language["code"])
        users_sec.append(KeyValueItem(Bold(language["code"].upper()), Code(len(users))))

    groups_sec = Section(
        "Korone Groups", KeyValueItem(Bold("All"), Code(groups_count[0]))
    )
    for lang in LANGUAGES.values():
        language = lang["language_info"]
        groups = await filter_chats_by_language(language=language["code"])
        groups_sec.append(
            KeyValueItem(Bold(language["code"].upper()), Code(len(groups)))
        )

    doc.append(users_sec)
    doc.append(groups_sec)
    await message.reply_text(doc)


@Korone.on_message(filters.cmd("broadcast") & filters.sudo)
async def broadcast(bot: Korone, message: Message):
    reply = message.reply_to_message
    args = get_args(message).split(" ")

    to = args[0]
    language = args[1]

    media = message.photo or message.animation or message.document or message.video
    text = " ".join((message.text or message.caption).split()[3:])
    if bool(reply):
        media = (
            reply.photo
            or reply.sticker
            or reply.animation
            or reply.document
            or reply.video
        )
        text = reply.text or reply.caption

    if not media:
        if text is None or len(text) == 0:
            await message.reply_text("The message cannot be empty.")
            return

    chats = []
    if to in ["groups", "all"]:
        chats += [
            chat["id"] for chat in await filter_chats_by_language(language=language)
        ]
    if to in ["users", "all"]:
        chats += [
            user["id"] for user in await filter_users_by_language(language=language)
        ]

    if len(chats) == 0:
        await message.reply_text("No chat was found, check if everything is right.")
    else:
        sent = await message.reply_text("The alert is being sent, please wait...")

        success = []
        failed = []
        for chat in chats:
            # if chat in CHATS.values():
            #    continue

            try:
                if isinstance(media, Animation):
                    await bot.send_animation(chat, media.file_id, text)
                elif isinstance(media, Document):
                    await bot.send_document(
                        chat, media.file_id, caption=text, force_document=True
                    )
                elif isinstance(media, Photo):
                    await bot.send_photo(chat, media.file_id, text)
                elif isinstance(media, Video):
                    await bot.send_video(chat, media.file_id, text)
                elif isinstance(media, Sticker):
                    await bot.send_sticker(chat, media.file_id)
                else:
                    await bot.send_message(chat, text)
                success.append(chat)
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except BaseException:
                failed.append(chat)

        await sent.edit_text(
            f"The alert was successfully sent to <code>{success}</code> chats "
            f"and failed to send in <code>{failed}</code> chats."
        )
