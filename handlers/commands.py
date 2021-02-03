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

import platform
import html
import re
import os
from datetime import datetime

import kantex
import youtube_dl
import pyrogram
import pyromod
from config import prefix
from kantex.html import Bold, Code, KanTeXDocument, KeyValueItem, Section, SubSection
from search_engine_parser import GoogleSearch, BingSearch
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from handlers.pm_menu import about_text
from handlers.utils.httpx import http
from . import COMMANDS_HELP

COMMANDS_HELP["commands"] = {
    "text": "Este é meu módulo principal de comandos.",
    "commands": {},
}

ydl = youtube_dl.YoutubeDL(
    {"outtmpl": "dls/%(title)s.%(ext)s", "format": "140", "noplaylist": True}
)


def pretty_size(size):
    units = ["B", "KB", "MB", "GB"]
    unit = 0
    while size >= 1024:
        size /= 1024
        unit += 1
    return "%0.2f %s" % (size, units[unit])


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


@Client.on_message(filters.cmd(command="about", action="Informações sobre o bot."))
async def about_cmd(c: Client, m: Message):
    await m.reply_text(about_text, disable_web_page_preview=True)


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
        command="ytdl (?P<search>.+)", action="Baixe vídeo do YouTube com youtube-dl."
    )
)
async def youtube(c: Client, m: Message):
    text = m.matches[0]["search"]
    if text:
        sent_id = await m.reply_text("Obtendo informações do vídeo...")
        try:
            if re.match(
                r"^(https?://)?(youtu\.be/|(m\.|www\.)?youtube\.com/watch\?v=).+",
                text,
            ):
                yt = ydl.extract_info(text, download=False)
            else:
                yt = ydl.extract_info("ytsearch:" + text, download=False)["entries"][0]
            for f in yt["formats"]:
                if f["format_id"] == "140":
                    fsize = f["filesize"] or 0
            name = yt["title"]
        except Exception as e:
            return await sent_id.edit_text("Ocorreu um erro.\n\n" + str(e))
        if not fsize > 52428800:
            if " - " in name:
                performer, title = name.rsplit(" - ", 1)
            else:
                performer = yt.get("creator") or yt.get("uploader")
                title = name
            await sent_id.edit_text(
                "Baixando <code>{}</code> do YouTube...\n({})".format(
                    name, pretty_size(fsize)
                )
            )
            ydl.download(["https://www.youtube.com/watch?v=" + yt["id"]])
            await sent_id.edit_text("Enviando áudio...")
            await c.send_chat_action(chat_id=m.chat.id, action="upload_audio")
            await c.send_audio(
                chat_id=m.chat.id,
                audio=open(ydl.prepare_filename(yt), "rb"),
                performer=performer,
                title=title,
                duration=yt["duration"],
            )
            os.remove(ydl.prepare_filename(yt))
            await sent_id.delete()
        else:
            await sent_id.edit_text(
                f"Ow, o arquivo resultante ({pretty_size(fsize)}) ultrapassa o meu limite de 50 MB",
            )

    else:
        await m.reply_text("<b>Uso:</b> /ytdl URL do vídeo ou nome")

    return True


# @Client.on_message(filters.regex(r"^/\w+") & filters.private, group=-1)
# async def none_command(c: Client, m: Message):
#     if if re.match(r"^(\/start|\/about|\/user|\/cat|\/py|\/echo|\/ping|\/copy|\/help|\/reboot|\/copy|\/upgrade|\/shutdown|korone,)", m.text):
#         m.continue_propagation()
#     react = random.choice(NONE_CMD)
#     await m.reply_text(react)
