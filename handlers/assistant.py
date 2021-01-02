import random

from pyrogram import Client, filters
from pyrogram.types import Message

from handlers.utils.random import NONE_CMD, HELLO, REACTIONS, CATCH_REACT


@Client.on_message(filters.regex(r"(?i)^Korone, gire um dado$"))
async def dice(c: Client, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(
        f"O dado parou no número {dicen.dice.value}")


@Client.on_message(filters.regex(r"(?i)^Korone, remova ele$") & filters.group)
async def kick(c: Client, m: Message):
    await c.kick_chat_member(m.chat.id, m.reply_to_message.from_user.id)
    await m.chat.unban_member(m.reply_to_message.from_user.id)
    await m.reply_animation(
        animation="https://media1.giphy.com/media/MZqLlWvzkkMCc/giphy.gif",
        quote=True)


@Client.on_message(filters.regex(r"(?i)^Korone, me d(ê|e) um cookie$"))
async def give_me_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^")
                       .format(m.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, d(ê|e) um cookie$") & filters.reply)
async def give_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^")
                       .format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, qual o nome dele$") & filters.reply)
async def tell_name(c: Client, m: Message):
    await m.reply_text(("O nome dele é {}! ^^")
                       .format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, pegue ele$") & filters.reply)
async def catch_him(c: Client, m: Message):
    react = random.choice(CATCH_REACT)
    reaction = random.choice(REACTIONS)
    await m.reply_text((react + reaction)
                       .format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone,"))
async def unknown_cmd(c: Client, m: Message):
    react = random.choice(NONE_CMD)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^Korone$"))
async def hello(c: Client, m: Message):
    react = random.choice(HELLO)
    await m.reply_text((react).format(m.from_user.first_name))
