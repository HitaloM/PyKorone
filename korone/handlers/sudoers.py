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

import os
import io
import sys
import asyncio
import traceback
from meval import meval
from typing import Dict

from pyrogram import Client, filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message, CallbackQuery

from korone.config import OWNER, SUDOERS, prefix
from korone.database import Chats


@Client.on_message(filters.cmd("(sh(eel)?|term(inal)?) ") & filters.user(OWNER))
async def on_terminal_m(c: Client, m: Message):
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
            await c.send_document(chat_id=m.chat.id, document=document)
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@Client.on_message(filters.cmd("ev(al)? ") & filters.user(SUDOERS))
async def on_eval_m(c: Client, m: Message):
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
            await c.send_document(chat_id=m.chat.id, document=document)
        else:
            output_message += f"<b>Output\n&gt;</b> {output}"
    await sm.edit_text(output_message)


@Client.on_message(filters.cmd("ex(ec(ute)?)? ") & filters.user(SUDOERS))
async def on_execute_m(c: Client, m: Message):
    command = m.text.split()[0]
    code = m.text[len(command) + 1 :]
    sm = await m.reply_text("Running...")
    function = """
async def _aexec_(c: Client, m: Message):
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


@Client.on_message(filters.command("reboot", prefix) & filters.user(SUDOERS))
async def restart(c: Client, m: Message):
    await m.reply_text("Reiniciando...")
    args = [sys.executable, "-m", "korone"]
    if "--no-update" in sys.argv:
        args.append("--no-update")
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
            else:
                if ":" in line:
                    key, value = line.split(": ")
                    commits[last_commit][key] = value
    return commits


@Client.on_message(filters.command("upgrade", prefix) & filters.user(SUDOERS))
async def upgrade(c: Client, m: Message):
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


@Client.on_callback_query(filters.regex("^upgrade") & filters.user(SUDOERS))
async def upgrade_cb(c: Client, cq: CallbackQuery):
    await cq.message.edit_text("Atualizando...")
    proc = await asyncio.create_subprocess_shell(
        "git pull --no-edit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0].decode()
    if proc.returncode == 0:
        await cq.message.edit_text("Reiniciando...")
        args = [sys.executable, "-m", "korone"]
        os.execv(sys.executable, args)
    else:
        lines = stdout.split("\n")
        error = "".join(f"<code>{line}</code>\n" for line in lines)
        await cq.message.edit_text(
            f"Atualização falhou (process exited with {proc.returncode}):\n{error}"
        )


@Client.on_message(filters.command("shutdown", prefix) & filters.user(OWNER))
async def shutdown(c: Client, m: Message):
    await m.reply_text("Adeus...")
    sys.exit()


@Client.on_message(filters.cmd("(broadcast|announcement) ") & filters.user(SUDOERS))
async def broadcast(c: Client, m: Message):
    sm = await m.reply_text("Fazendo seu anúncio...")
    command = m.text.split()[0]
    text = m.text[len(command) + 1 :]
    chats = await Chats.all()
    success = []
    fail = []
    for chat in chats:
        try:
            if await c.send_message(chat.id, text):
                success.append(chat.id)
            else:
                fail.append(chat.id)
        except BaseException:
            fail.append(chat.id)
    await sm.edit_text(
        f"Anúncio feito com sucesso! Sua mensagem foi enviada em um total de <code>{len(success)}</code> grupos e falhou o envio em <code>{len(fail)}</code> grupos."
    )


@Client.on_message(filters.command("chat", prefix) & filters.user(SUDOERS))
async def chat_info(c: Client, m: Message):
    try:
        chat = await c.get_chat(m.command[1])
    except BadRequest as e:
        return await m.reply_text(f"<b>Erro!</b>\n<code>{e}</code>")

    if chat.type == "private":
        await m.reply_text("Este chat é privado!")
    else:
        text = f"<b>Título:</b> {chat.title}\n"
        if chat.username:
            text += f"<b>Username:</b> <code>{chat.username}</code>\n"
        text += f"<b>ID:</b> <code>{chat.id}</code>\n"
        text += f"<b>Link:</b> {chat.invite_link}\n"
        text += f"<b>Membros:</b> <code>{chat.members_count}</code>\n"
        if chat.description:
            text += f"\n<b>Descrição:</b>\n<i>{chat.description}</i>"

        await m.reply_text(text)


@Client.on_message(filters.cmd(command="echo (?P<text>.+)") & filters.user(SUDOERS))
async def echo(c: Client, m: Message):
    text = m.matches[0]["text"]
    chat_id = m.chat.id
    kwargs = {}
    reply = m.reply_to_message
    if reply:
        kwargs["reply_to_message_id"] = reply.message_id
    try:
        await m.delete()
    except BaseException:
        pass
    await c.send_message(chat_id=chat_id, text=text, **kwargs)
