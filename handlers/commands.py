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

import requests
import platform
import html
import re
import os
import io
from datetime import datetime

import kantex
import pyrogram
import pyromod
from config import prefix
from kantex.html import Bold, Code, KanTeXDocument, KeyValueItem, Section, SubSection
from bs4 import BeautifulSoup as bs
from PIL import Image
from search_engine_parser import GoogleSearch, BingSearch
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from utils import http
from . import COMMANDS_HELP

GROUP = "general"

COMMANDS_HELP[GROUP] = {
    "name": "Geral",
    "text": "Este é meu módulo principal de comandos.",
    "commands": {},
    "help": True,
}


def cleanhtml(raw_html):
    cleanr = re.compile("<.*?>")
    cleantext = re.sub(cleanr, "", raw_html)
    return cleantext


def escape_definition(definition):
    for key, value in definition.items():
        if isinstance(value, str):
            definition[key] = html.escape(cleanhtml(value))
    return definition


@Client.on_message(
    filters.cmd(command="pypi (?P<search>.+)", action="Pesquisa de módulos no PyPI.")
)
async def pypi(c: Client, m: Message):
    text = m.matches[0]["search"]
    r = await http.get(f"https://pypi.org/pypi/{text}/json")
    if r.status_code == 200:
        json = r.json()
        pypi_info = escape_definition(json["info"])
        message = (
            "<b>%s</b> by <i>%s %s</i>\n"
            "Platform: <b>%s</b>\n"
            "Version: <b>%s</b>\n"
            "License: <b>%s</b>\n"
            "Summary: <b>%s</b>\n"
            % (
                pypi_info["name"],
                pypi_info["author"],
                f"&lt;{pypi_info['author_email']}&gt;"
                if pypi_info["author_email"]
                else "",
                pypi_info["platform"] or "Not specified",
                pypi_info["version"],
                pypi_info["license"] or "None",
                pypi_info["summary"],
            )
        )
        if pypi_info["home_page"] and pypi_info["home_page"] != "UNKNOWN":
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Package Home Page", url=pypi_info["home_page"]
                        )
                    ]
                ]
            )
        else:
            kb = None
        await m.reply_text(
            message,
            disable_web_page_preview=True,
            reply_markup=kb,
        )
    else:
        await m.reply_text(
            f"Cant find <b>{text}</b> in pypi (Returned code was {r.status_code})",
            disable_web_page_preview=True,
        )
    return


@Client.on_message(
    filters.cmd(command="ping", action="Verifique a velocidade de resposta do bot.")
)
async def ping(c: Client, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Client.on_message(
    filters.cmd(command="user", action="Retorna algumas informações do usuário.")
    & filters.reply
)
async def user_info(c: Client, m: Message):
    user_id = m.reply_to_message.from_user.id
    first_name = m.reply_to_message.from_user.first_name
    try:
        last_name = m.reply_to_message.from_user.last_name
    except Exception:
        last_name = None
    username = m.reply_to_message.from_user.username
    doc = KanTeXDocument(
        Section(
            first_name,
            SubSection(
                "Geral",
                KeyValueItem("id", Code(user_id)),
                KeyValueItem("first_name", Code(first_name)),
                KeyValueItem("last_name", Code(last_name)),
                KeyValueItem("username", Code(username)),
            ),
        )
    )
    await m.reply_text(doc)


@Client.on_message(
    filters.cmd(
        command="copy",
        action="Comando originalmente para testes mas que também é divertido.",
    )
    & filters.reply
)
async def copy(c: Client, m: Message):
    try:
        await c.copy_message(
            chat_id=m.chat.id,
            from_chat_id=m.chat.id,
            message_id=m.reply_to_message.message_id,
        )
    except BaseException:
        return


@Client.on_message(
    filters.cmd(command="echo (?P<text>.+)", action="Fale através do bot.")
)
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


@Client.on_message(filters.command("py", prefix))
async def dev(c: Client, m: Message):
    source_url = "git.io/JtmRH"
    doc = Section(
        "PyKorone Bot",
        KeyValueItem(Bold("Source"), source_url),
        KeyValueItem(Bold("Pyrogram version"), pyrogram.__version__),
        KeyValueItem(Bold("Pyromod version"), pyromod.__version__),
        KeyValueItem(Bold("Python version"), platform.python_version()),
        KeyValueItem(Bold("KanTeX version"), kantex.__version__),
        KeyValueItem(Bold("System version"), c.system_version),
    )
    await m.reply_text(doc, disable_web_page_preview=True)


@Client.on_message(filters.cmd(command="cat", action="Imagens de gatinhos."))
async def cat(c: Client, m: Message):
    response = await http.get("https://api.thecatapi.com/v1/images/search")
    cats = response.json
    await m.reply_photo(cats()[0]["url"], caption="Meow!! (^つωฅ^)")


@Client.on_message(filters.cmd(command="dog", action="Imagens de cachorrinhos."))
async def dog(c: Client, m: Message):
    response = await http.get("https://random.dog/woof.json")
    dogs = response.json()
    await m.reply_photo(dogs["url"], caption="Woof!! U・ᴥ・U")


@Client.on_message(
    filters.cmd(
        command="google (?P<search>.+)",
        action="Faça uma pesquisa no Google através do bot.",
    )
)
async def google(c: Client, m: Message):
    query = m.matches[0]["search"]
    search_args = (str(query), 1)
    googsearch = GoogleSearch()
    gresults = await googsearch.async_search(*search_args)
    msg = ""
    for i in range(1, 6):
        try:
            title = gresults["titles"][i]
            link = gresults["links"][i]
            desc = gresults["descriptions"][i]
            msg += f"{i}. <a href='{link}'>{title}</a>\n<code>{desc}</code>\n\n"
        except IndexError:
            break
    await m.reply_text(
        "<b>Consulta:</b>\n<code>"
        + html.escape(query)
        + "</code>\n\n<b>Resultados:</b>\n"
        + msg,
        disable_web_page_preview=True,
    )


@Client.on_message(
    filters.cmd(
        command="bing (?P<search>.+)",
        action="Faça uma pesquisa no Bing através do bot.",
    )
)
async def bing(c: Client, m: Message):
    query = m.matches[0]["search"]
    search_args = (str(query), 1)
    bingsearch = BingSearch()
    bresults = await bingsearch.async_search(*search_args)
    msg = ""
    for i in range(1, 6):
        try:
            title = bresults["titles"][i]
            link = bresults["links"][i]
            desc = bresults["descriptions"][i]
            msg += f"{i}. <a href='{link}'>{html.escape(title)}</a>\n<code>{html.escape(desc)}</code>\n\n"
        except IndexError:
            break
    await m.reply_text(
        "<b>Consulta:</b>\n<code>"
        + html.escape(query)
        + "</code>\n\n<b>Resultados:</b>\n"
        + msg,
        disable_web_page_preview=True,
    )


@Client.on_message(
    filters.cmd(
        command="stickers (?P<search>.+)",
        action="Pesquise stickers.",
    )
)
async def cb_sticker(c: Client, m: Message):
    args = m.matches[0]["search"]

    text = requests.get("https://combot.org/telegram/stickers?q=" + args).text
    soup = bs(text, "lxml")
    results = soup.find_all("a", {"class": "sticker-pack__btn"})
    titles = soup.find_all("div", "sticker-pack__title")
    if not results:
        await m.reply_text("Nenhum resultado encontrado!")
        return

    reply = f"Stickers for <b>{args}</b>:"
    for result, title in zip(results, titles):
        link = result["href"]
        reply += f"\n - <a href='{link}'>{title.get_text()}</a>"
    await m.reply_text(reply, disable_web_page_preview=True)


@Client.on_message(
    filters.cmd(
        command="color (?P<hex>.+)",
        action="Obtenha uma cor em sticker através do hex ou nome.",
    )
)
async def stickcolor(c: Client, m: Message):
    args = m.matches[0]["hex"]
    color_sticker = stickcolorsync(args)

    if color_sticker:
        await m.reply_sticker(color_sticker)
    else:
        await m.reply_text(
            f"<code>{args}</code> é uma cor inválida, use <code>#hex</code> ou o nome da cor."
        )


def stickcolorsync(color):
    try:
        image = Image.new("RGBA", (512, 512), color)
    except:
        try:
            image = Image.new("RGBA", (512, 512), "#" + color)
        except:
            return

    image_stream = io.BytesIO()
    image_stream.name = "sticker.webp"
    image.save(image_stream, "WebP")
    image_stream.seek(0)

    return image_stream
