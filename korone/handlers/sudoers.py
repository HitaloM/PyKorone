# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import io
import os
import platform
import signal
import sys
import traceback
from datetime import datetime, timezone
from typing import Dict

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
from korone.utils import client_restart, modules


@Korone.on_message(filters.cmd("(sh(eel)?|term(inal)?) ") & filters.user(OWNER))
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


@Korone.on_message(filters.sudoer & filters.cmd("ev(al)? "))
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


@Korone.on_message(filters.sudoer & filters.cmd("ex(ec(ute)?)? "))
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


@Korone.on_message(filters.sudoer & filters.cmd("reboot"))
async def restart(c: Korone, m: Message):
    m = await m.reply_text("Reiniciando...")
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


@Korone.on_message(filters.sudoer & filters.cmd("upgrade"))
async def upgrade(c: Korone, m: Message):
    sm = await m.reply_text("Verificando...")
    await (await asyncio.create_subprocess_shell("git fetch origin")).communicate()
    proc = await asyncio.create_subprocess_shell(
        "git log HEAD..origin/main",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()
    if proc.returncode == 0:
        if len(stdout) <= 0:
            return await sm.edit_text("Não há nada para atualizar.")
        changelog = "<b>Changelog</b>:\n"
        commits = parse_commits(stdout)
        for hash, commit in commits.items():
            changelog += f"  - [<code>{hash[:7]}</code>] {commit['title']}\n"
        changelog += f"\n<b>New commits count</b>: <code>{len(commits)}</code>."
        keyboard = [[("🆕 Atualizar", "upgrade")]]
        await sm.edit_text(changelog, reply_markup=c.ikb(keyboard))
    else:
        lines = stdout.split("\n")
        error = "".join(f"<code>{line}</code>\n" for line in lines)
        await sm.edit_text(
            f"Falha na atualização (process exited with {proc.returncode}):\n{error}"
        )


@Korone.on_callback_query(filters.sudoer & filters.regex("^upgrade"))
async def upgrade_cb(c: Korone, cq: CallbackQuery):
    await cq.edit_message_reply_markup({})
    sent = await cq.message.reply_text("Atualizando...")
    proc = await asyncio.create_subprocess_shell(
        "git pull --no-edit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()
    if proc.returncode == 0:
        await sent.edit_text("Reiniciando...")
        args = [sys.executable, "-m", "korone"]
        os.execv(sys.executable, args)
    else:
        lines = stdout.split("\n")
        error = "".join(f"<code>{line}</code>\n" for line in lines)
        await sent.edit_text(
            f"Atualização falhou (process exited with {proc.returncode}):\n{error}"
        )


@Korone.on_message(filters.cmd("shutdown") & filters.user(OWNER))
async def shutdown(c: Korone, m: Message):
    await m.reply_text("Adeus...")
    os.kill(os.getpid(), signal.SIGINT)


@Korone.on_message(filters.sudoer & filters.cmd("echo (?P<text>.+)"))
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


@Korone.on_message(filters.sudoer & filters.cmd("copy$"))
async def copy(c: Korone, m: Message):
    try:
        await c.copy_message(
            chat_id=m.chat.id,
            from_chat_id=m.chat.id,
            message_id=m.reply_to_message.message_id,
        )
    except BadRequest as e:
        await m.reply_text(f"<b>Erro!</b>\n<code>{e}</code>")
        return


@Korone.on_message(filters.sudoer & filters.cmd("py"))
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


@Korone.on_message(filters.sudoer & filters.cmd("reload"))
async def modules_reload(c: Korone, m: Message):
    sent = await m.reply_text("<b>Recarregando módulos...</b>")
    first = datetime.now()
    modules.reload(c)
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Módulos recarregados em</b> <code>{time}ms</code>!")
