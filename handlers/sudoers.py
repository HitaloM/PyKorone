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
from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.command("reboot", prefix) & filters.user(SUDOERS))
async def restart(c: Client, m: Message):
    await m.reply_text("Reiniciando...")
    os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(filters.command("upgrade", prefix) & filters.user(SUDOERS))
async def upgrade(c: Client, m: Message):
    sm = await m.reply_text("Atualizando...")
    proc = await asyncio.create_subprocess_shell(
        "git pull --no-edit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout = (await proc.communicate())[0]
    if proc.returncode == 0:
        if "Already up to date." in stdout.decode():
            await sm.edit_text("Não há nada para atualizar.")
        else:
            await sm.edit_text("Reiniciando...")
            args = [sys.executable, "bot.py"]
            os.execl(sys.executable, *args)
    else:
        await sm.edit_text(
            "Atualização falhou (process exited with {proc.returncode}):\n{stdout.decode()}"
        )
        proc = await asyncio.create_subprocess_shell("git merge --abort")
        await proc.communicate()


@Client.on_message(filters.command("shutdown", prefix) & filters.user(OWNER))
async def shutdown(c: Client, m: Message):
    await m.reply_text("Adeus...")
    sys.exit()
