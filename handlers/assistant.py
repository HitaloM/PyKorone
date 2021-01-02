import html
import random

from pyrogram import Client, filters
from pyrogram.types import Message

NONE_CMD = (
    "Nani...? :'c",
    "....?",
    "*jiiii*",
    "O que?! >~<",
    "*encara o vazio*",
    "Hmm... :cc",
    "Hmm... :'c",
    "OwO o que é isso??",
    "Compreendo!U~U\n*realmente não entendo*"
)

HELLO = (
    "À sua disposição {}! ^^",
    "Sim? *^^^*",
    "Nya! Ao seu serviço ~",
    "Sim {}? *^*",
    "Sim? *A*",
    "{}! Eu estou aqui! :3",
    "Posso te ajudar {}? uwu",
    "{}! Estou aqui! :3"
)


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


@Client.on_message(filters.regex(r"(?i)^Korone, me dê um cookie$"))
async def give_me_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^").format(m.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, dê um cookie$") & filters.reply)
async def give_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^").format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone,"))
async def unknown_cmd(c: Client, m: Message):
    react = random.choice(NONE_CMD)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^Korone$"))
async def hello(c: Client, m: Message):
    react = random.choice(HELLO)
    await m.reply_text((react).format(m.from_user.first_name))
