import html
import random

from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.regex(r"(?i)^Korone, gire um dado$"))
async def dice(c: Client, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(
        f"O dado parou no número {dicen.dice.value}")


@Client.on_message(filters.regex(r"(?i)^Korone, remova ele$") & filters.group)
async def kick(c: Client, m: Message):
    await c.kick_chat_member(m.chat.id, m.reply_to_message.from_user.id)
    await m.chat.unban_member(m.reply_to_message.from_user.id)
    await m.reply_animation(animation="https://media1.giphy.com/media/MZqLlWvzkkMCc/giphy.gif", quote=True)
