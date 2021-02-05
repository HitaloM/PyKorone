# This file is part of Korone (Telegram Bot)

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
import sys
import asyncio

from config import OWNER, SUDOERS, prefix
from pyromod.helpers import ikb
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from typing import Dict


@Client.on_message(filters.command("reboot", prefix) & filters.user(SUDOERS))
async def restart(c: Client, m: Message):
    await m.reply_text("Reiniciando...")
    os.execl(sys.executable, sys.executable, *sys.argv)


def parse_commits(log: str) -> Dict:
    commits = {}
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
        if len(stdout) > 0:
            changelog = "<b>Changelog</b>:\n"
            commits = parse_commits(stdout)
            for hash, commit in commits.items():
                changelog += f"  - [<code>{hash[:7]}</code>] {commit['title']}\n"
            changelog += f"\n<b>New commits count</b>: <code>{len(commits)}</code>."
            keyboard = [[("🆕 Atualizar", "upgrade")]]
            await sm.edit_text(changelog, reply_markup=ikb(keyboard))
        else:
            return await sm.edit_text("Não há nada para atualizar.")
    else:
        error = ""
        lines = stdout.split("\n")
        for line in lines:
            error += f"<code>{line}</code>\n"
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
        args = [sys.executable, "-m", "bot"]
        os.execv(sys.executable, args)
    else:
        error = ""
        lines = stdout.split("\n")
        for line in lines:
            error += f"<code>{line}</code>\n"
        await cq.message.edit_text(
            f"Atualização falhou (process exited with {proc.returncode}):\n{error}"
        )


@Client.on_message(filters.command("shutdown", prefix) & filters.user(OWNER))
async def shutdown(c: Client, m: Message):
    await m.reply_text("Adeus...")
    sys.exit()
