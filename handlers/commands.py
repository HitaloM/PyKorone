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
    await m.reply_text(
        """
<i>Mais informações serão adicionadas neste comando!</i>

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
