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
import html
import re
import io
from bs4 import BeautifulSoup as bs
from PIL import Image
from search_engine_parser import GoogleSearch, BingSearch
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from utils import http
from . import COMMANDS_HELP

GROUP = "utils"

COMMANDS_HELP[GROUP] = {
    "name": "Utilidades",
    "text": "Este é meu módulo de comandos utilitários.",
    "commands": {},
    "help": True,
}


def cleanhtml(raw_html):
    cleanr = re.compile("<.*?>")
    return re.sub(cleanr, "", raw_html)


def escape_definition(definition):
    for key, value in definition.items():
        if isinstance(value, str):
            definition[key] = html.escape(cleanhtml(value))
    return definition


@Client.on_message(
    filters.cmd(
        command="pypi (?P<search>.+)",
        action="Pesquisa de módulos no PyPI.",
        group=GROUP,
    )
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
    filters.cmd(
        command="google (?P<search>.+)",
        action="Faça uma pesquisa no Google através do bot.",
        group=GROUP,
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
        group=GROUP,
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
        command="stickers (?P<search>.+)", action="Pesquise stickers.", group=GROUP
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
        group=GROUP,
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
    except BaseException:
        try:
            image = Image.new("RGBA", (512, 512), "#" + color)
        except BaseException:
            return

    image_stream = io.BytesIO()
    image_stream.name = "sticker.webp"
    image.save(image_stream, "WebP")
    image_stream.seek(0)

    return image_stream
