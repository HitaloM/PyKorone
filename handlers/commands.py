import os
import platform
import pyrogram
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message

from config import prefix


@Client.on_message(filters.command("ping", prefix))
async def ping(c: Client, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    await sent.edit_text(f"<b>Pong!</b> <code>{(second - first).microseconds / 1000}</code>ms")


@Client.on_message(filters.command("dev", prefix))
async def dev(c: Client, m: Message):
    python_version = platform.python_version()
    pyrogram_version = pyrogram.__version__ 
    await m.reply_text(
        f"""
<b>Korone Info:</b>
<b>Python:</b> <code>{python_version}</code>
<b>Pyrogram:</b> <code>{pyrogram_version}</code>

Feito com ❤️ por @Hitalo
    """
    )


@Client.on_message(filters.command("start", prefix))
async def start(c: Client, m: Message):
    await m.reply_text(
        """
Oi, eu sou o <b>Korone</b>, um bot interativo que adora participar de grupos! ^^

Você pode entender como eu funciono com o comando /help
    """
    )
