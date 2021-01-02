import random

from pyrogram import Client, filters
from pyrogram.types import Message

FUCK_REACT = (
    "((ﾉ◉Д◉)ﾉ ﾐ ┸━┸",
    "(ﾉ≧∇≦)ﾉ ﾐ ┸━┸"
)

AYY_REACT = (
    "lmao",
    "lol"
)

UWU_REACT = (
    "UWU",
    "UwU",
    "uwu"
)

DOGE_REACT = (
    "₍^•ﻌ•^₎",
    "ʕ •ᴥ•ʔ"
)

BANHAMMERS = (
    "CAACAgQAAx0CT2XwHwACV-Nf78g1TSCO_mWtKhTbpOdalpdNHAACzwEAAgYlKAMdkZFHZv_nNR4E",
    "CAACAgQAAx0CT2XwHwACWAABX-_J6flwJKzep9rYUQttGXJzcwQAAtEBAAIGJSgDDFVJta1mslAeBA",
    "CAACAgQAAx0CT2XwHwACWDlf78oRiyeopP7i4rPx_k62hLyOGgACxgEAAgYlKANkSj4WKRcTjx4E")


@Client.on_message(filters.regex(r"(?i)^koto$"))
async def koto(c: Client, m: Message):
    await c.send_sticker(chat_id=m.chat.id,
                         reply_to_message_id=m.message_id,
                         sticker="CAACAgQAAx0CT2XwHwACWD5f78orS_P4vhpvK29jDz2LE4Ju4QAC2QEAAgYlKAOlyAtKtsFCAAEeBA")


@Client.on_message(filters.regex(r"(?i)^banhammer$"))
async def banhammer(c: Client, m: Message):
    react = random.choice(BANHAMMERS)
    await c.send_sticker(chat_id=m.chat.id,
                         reply_to_message_id=m.message_id,
                         sticker=react)


@Client.on_message(filters.regex(r"(?i)^ban$"))
async def banhammer(c: Client, m: Message):
    react = "CAACAgEAAx0CT2XwHwACWb5f8IhBw1kQL4BZ5C-W2xQUb8TmLQACqwADMWm8NnADxrv2ioYwHgQ"
    await c.send_sticker(chat_id=m.chat.id,
                         reply_to_message_id=m.message_id,
                         sticker=react)


@Client.on_message(filters.regex(r"(?i)^yee$"))
async def yee(c: Client, m: Message):
    await m.reply_text("o(≧∇≦)o")


@Client.on_message(filters.regex(r"(?i)^rip$"))
async def rip(c: Client, m: Message):
    await m.reply_text("❀◟(ó ̯ ò, )")


@Client.on_message(filters.regex(r"(?i)^f$"))
async def press_f(c: Client, m: Message):
    await m.reply_text("F")


@Client.on_message(filters.regex(r"(?i)^python$"))
async def python(c: Client, m: Message):
    await m.reply_text("is a snake 🐍")


@Client.on_message(filters.regex(r"(?i)^sleepy$"))
async def sleepy(c: Client, m: Message):
    await m.reply_text(". . . (∪｡∪)｡｡｡zzzZZ")


@Client.on_message(filters.regex(r"(?i)^grr+$"))
async def grr(c: Client, m: Message):
    await m.reply_text("😡")


@Client.on_message(filters.regex(r"(?i)^porra$"))
async def fuck(c: Client, m: Message):
    react = random.choice(FUCK_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^doge|doggo$"))
async def doge(c: Client, m: Message):
    react = random.choice(DOGE_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^ayy$"))
async def ayy(c: Client, m: Message):
    react = random.choice(AYY_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^uwu$"))
async def uwu(c: Client, m: Message):
    react = random.choice(UWU_REACT)
    await m.reply_text(react)
