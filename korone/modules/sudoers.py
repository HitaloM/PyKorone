# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import asyncio
import io
import os
import platform
import signal
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict, Iterable

import humanize
import psutil
import pyrogram
from kantex.html import Bold, Code, KeyValueItem, Section
from meval import meval
from pyrogram import filters
from pyrogram.errors import BadRequest
from pyrogram.types import CallbackQuery, Message

import korone
from korone.config import OWNER
from korone.korone import Korone
from korone.utils import client_restart
from korone.utils.args import get_args_str, need_args_dec


@Korone.on_message(filters.cmd(r"(sh(eel)?|term(inal)?) ") & filters.user(OWNER))
async def on_terminal_m(c: Korone, m: Message):
    command = m.text.split()[0]
    code = m.text[len(command) + 1 :]
    sm = await m.reply_text("Running...")
    proc = await asyncio.create_subprocess_shell(
        code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0]
    lines = stdout.decode().split("\n")
    output = "".join(f"<code>{line}</code>\n" for line in lines)
    output_message = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"
    if len(output) > 0:
        if len(output) > (4096 - len(output_message)):
            document = io.BytesIO(
                (output.replace("<code>", "").replace("</code>", "")).encode()
            )
            document.name = "output.txt"
            await c.send_document(
                chat_id=m.chat.id, document=document, reply_to_message_id=m.message_id
            )
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@Korone.on_message(filters.sudoer & filters.cmd(r"ev(al)? "))
async def on_eval_m(c: Korone, m: Message):
    command = m.text.split()[0]
    eval_code = m.text[len(command) + 1 :]
    sm = await m.reply_text("Running...")
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
            await c.send_document(
                chat_id=m.chat.id, document=document, reply_to_message_id=m.message_id
            )
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@Korone.on_message(filters.sudoer & filters.cmd(r"ex(ec(ute)?)? "))
async def on_execute_m(c: Korone, m: Message):
    command = m.text.split()[0]
    code = m.text[len(command) + 1 :]
    sm = await m.reply_text("Running...")
    function = """
async def _aexec_(c: Korone, m: Message):
    """
    for line in code.split("\n"):
        function += f"\n    {line}"
    exec(function)
    try:
        await locals()["_aexec_"](c, m)
    except BaseException:
        error = traceback.format_exc()
        await sm.edit_text(
            f"An error occurred while running the code:\n<code>{error}</code>"
        )
        return
    output_message = f"<b>Input\n&gt;</b> <code>{code}</code>\n\n"
    await sm.edit_text(output_message)


@Korone.on_message(filters.sudoer & filters.cmd(r"reboot"))
async def restart(c: Korone, m: Message):
    m = await m.reply_text("Restaring...")
    asyncio.get_event_loop().create_task(client_restart(c, m))


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


@Korone.on_message(filters.sudoer & filters.cmd(r"upgrade"))
async def upgrade(c: Korone, m: Message):
    sm = await m.reply_text("Checking...")
    await (await asyncio.create_subprocess_shell("git fetch origin")).communicate()
    proc = await asyncio.create_subprocess_shell(
        "git log HEAD..origin/main",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()
    if proc.returncode == 0:
        if len(stdout) <= 0:
            return await sm.edit_text("There is nothing to update.")
        changelog = "<b>Changelog</b>:\n"
        commits = parse_commits(stdout)
        for hash, commit in commits.items():
            changelog += f"  - [<code>{hash[:7]}</code>] {commit['title']}\n"
        changelog += f"\n<b>New commits count</b>: <code>{len(commits)}</code>."
        keyboard = [[("🆕 Upgrade", "upgrade")]]
        await sm.edit_text(changelog, reply_markup=c.ikb(keyboard))
    else:
        lines = stdout.split("\n")
        error = "".join(f"<code>{line}</code>\n" for line in lines)
        await sm.edit_text(
            f"Update failed (process exited with {proc.returncode}):\n{error}"
        )


@Korone.on_callback_query(filters.sudoer & filters.regex(r"^upgrade"))
async def upgrade_cb(c: Korone, cq: CallbackQuery):
    await cq.edit_message_reply_markup({})
    sent = await cq.message.reply_text("Updating...")
    proc = await asyncio.create_subprocess_shell(
        "git pull --no-edit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()
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


@Korone.on_message(filters.cmd(r"shutdown") & filters.user(OWNER))
async def shutdown(c: Korone, m: Message):
    await m.reply_text("Goodbye...")
    os.kill(os.getpid(), signal.SIGINT)


@Korone.on_message(filters.sudoer & filters.cmd(r"echo (?P<text>.+)"))
async def echo(c: Korone, m: Message):
    text = m.matches[0]["text"]
    kwargs = {}
    reply = m.reply_to_message
    if reply:
        kwargs["reply_to_message_id"] = reply.message_id
    try:
        await m.delete()
    except BadRequest:
        pass
    await c.send_message(chat_id=m.chat.id, text=text, **kwargs)


@Korone.on_message(filters.sudoer & filters.cmd(r"copy$"))
async def copy(c: Korone, m: Message):
    try:
        await c.copy_message(
            chat_id=m.chat.id,
            from_chat_id=m.chat.id,
            message_id=m.reply_to_message.message_id,
        )
    except BadRequest as e:
        await m.reply_text(f"<b>Error!</b>\n<code>{e}</code>")
        return


@Korone.on_message(filters.sudoer & filters.cmd(r"py"))
async def bot_info(c: Korone, m: Message):
    doc = Section(
        "PyKorone Bot",
        KeyValueItem(Bold("Source"), korone.__source__),
        KeyValueItem(Bold("Korone"), f"{korone.__version__} ({c.version_code})"),
        KeyValueItem(Bold("Pyrogram"), pyrogram.__version__),
        KeyValueItem(Bold("Python"), platform.python_version()),
    )
    await m.reply_text(doc, disable_web_page_preview=True)


@Korone.on_message(filters.sudoer & filters.cmd("sysinfo"))
async def system_info(c: Korone, m: Message):
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
    time_now = datetime.now().replace(tzinfo=timezone.utc)
    uptime = time_now - c.start_time

    doc = Section(
        "PyKorone System",
        KeyValueItem(Bold("OS"), Code(uname.system)),
        KeyValueItem(Bold("Node"), Code(uname.node)),
        KeyValueItem(Bold("Kernel"), Code(uname.release)),
        KeyValueItem(Bold("Arch"), Code(uname.machine)),
        KeyValueItem(Bold("CPU"), Code(cpu_usage)),
        KeyValueItem(Bold("RAM"), Code(f"{vm_used}/{vm_total}")),
        KeyValueItem(Bold("Swap"), Code(f"{sm_used}/{sm_total}")),
        KeyValueItem(Bold("Uptime"), Code(humanize.precisedelta(uptime))),
    )

    await m.reply_text(doc, disable_web_page_preview=True)


@Korone.on_message(
    filters.sudoer
    & filters.cmd(
        command=r"chat",
    )
)
@need_args_dec()
async def chat_info(c: Korone, m: Message):
    args = get_args_str(m)
    CHAT_TYPES: Iterable[str] = ("channel", "group", "supergroup")

    try:
        chat = await c.get_chat(args) if args else await c.get_chat(m.chat.id)
    except BadRequest as e:
        await m.reply_text(f"<b>Error!</b>\n<code>{e}</code>")
        return
    if chat.type not in CHAT_TYPES:
        await m.reply_text("This chat is private!")
        return

    if chat.type in CHAT_TYPES:
        text = "<b>Chat Information</b>:\n"
        text += f"Name: <code>{chat.title}</code>\n"
        text += f"ID: <code>{chat.id}</code>\n"
        if chat.username:
            text += f"Username: @{chat.username}\n"
        if chat.dc_id:
            text += f"Datacenter: <code>{chat.dc_id}</code>\n"
        text += f"Members: <code>{chat.members_count}</code>\n"
        if chat.id == m.chat.id:
            text += f"Messages: <code>{m.message_id}</code>\n"
        if chat.invite_link:
            text += f"Invitation link: {chat.invite_link}\n"
        if chat.description:
            text += f"\n<b>Description:</b>\n<code>{chat.description}</code>"

    await m.reply_text(text)
