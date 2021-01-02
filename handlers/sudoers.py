import os
import sys

from pyrogram import Client, filters
from pyrogram.types import Message

from config import SUDOERS, prefix


@Client.on_message(filters.command("reboot", prefix) & filters.user(SUDOERS))
async def restart(c: Client, m: Message):
    sent = await m.reply_text("Reiniciando...")
    os.execl(sys.executable, sys.executable, *sys.argv)
