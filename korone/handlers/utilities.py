# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

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

import re
import os
import html
import time
import datetime
import youtube_dl
from bs4 import BeautifulSoup as bs
from search_engine_parser import GoogleSearch, BingSearch

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from korone.utils import http, pretty_size
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.translator import tr, get_tr_lang
from korone.handlers.utils.misc import escape_definition
from korone.handlers.utils.image import stickcolorsync
from korone.handlers.utils.ytdl import extract_info


GROUP = "utils"

COMMANDS_HELP[GROUP] = {
    "name": "Utilidades",
    "text": "Este é meu módulo de comandos utilitários.",
    "commands": {},
    "help": True,
}


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
            "<b>%s</b> Por <i>%s %s</i>\n"
            "Plataforma: <b>%s</b>\n"
            "Versão: <b>%s</b>\n"
            "Licença: <b>%s</b>\n"
            "Resumo: <b>%s</b>\n"
            % (
                pypi_info["name"],
                pypi_info["author"],
                f"&lt;{pypi_info['author_email']}&gt;"
                if pypi_info["author_email"]
                else "",
                pypi_info["platform"] or "Não especificado",
                pypi_info["version"],
                pypi_info["license"] or "Nenhuma",
                pypi_info["summary"],
            )
        )
        if pypi_info["home_page"] and pypi_info["home_page"] != "UNKNOWN":
            keyboard = [[("Página inicial do pacote", pypi_info["home_page"], "url")]]
        else:
            keyboard = None
        await m.reply_text(
            message,
            disable_web_page_preview=True,
            reply_markup=c.ikb(keyboard),
        )
    else:
        await m.reply_text(
            f"Não consigo encontrar <b>{text}</b> no pypi (Código retornado foi {r.status_code})",
            disable_web_page_preview=True,
        )
    return


@Client.on_message(
    filters.cmd(
        command="google (?P<search>.+)",
        action="Faça uma pesquisa no Google através do korone.",
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
        action="Faça uma pesquisa no Bing através do korone.",
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
        command="cleanup",
        action="Banir contas excluídas do grupo.",
        group=GROUP,
    )
)
async def cleanup(c: Client, m: Message):
    member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)

    if member.status in ["administrator", "creator"]:
        deleted = []
        sent = await m.reply_text("Iniciando limpeza...")
        async for t in c.iter_chat_members(chat_id=m.chat.id, filter="all"):
            if t.user.is_deleted:
                try:
                    await c.kick_chat_member(m.chat.id, t.user.id)
                    deleted.append(t)
                except BaseException:
                    pass
        if len(deleted) > 0:
            await sent.edit_text("Removi todas as contas excluídas do grupo!")
        else:
            await sent.edit_text("Não há contas excluídas no grupo!")
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")


@Client.on_message(
    filters.cmd(
        command="stickers (?P<search>.+)", action="Pesquise stickers.", group=GROUP
    )
)
async def cb_sticker(c: Client, m: Message):
    args = m.matches[0]["search"]

    r = await http.get("https://combot.org/telegram/stickers?page=1&q=" + args)
    soup = bs(r.text, "lxml")
    main_div = soup.find("div", {"class": "sticker-packs-list"})
    results = main_div.find_all("a", {"class": "sticker-pack__btn"})
    titles = main_div.find_all("div", "sticker-pack__title")
    if not results:
        await m.reply_text("Nenhum resultado encontrado!")
        return

    text = f"Stickers de <b>{args}</b>:"
    for result, title in zip(results, titles):
        link = result["href"]
        text += f"\n - <a href='{link}'>{title.get_text()}</a>"
    await m.reply_text(text, disable_web_page_preview=True)


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


@Client.on_message(
    filters.cmd(
        command="ytdl(\s(?P<text>.+))?",
        action="Faça o Korone baixar um vídeo do YouTube e enviar no chat atual.",
        group=GROUP,
    )
)
async def on_ytdl(c: Client, m: Message):
    args = m.matches[0]["text"]
    user = m.from_user.id
    if m.reply_to_message and m.reply_to_message.text:
        url = m.reply_to_message.text
    elif m.text and args:
        url = args
    else:
        await m.reply_text("Por favor, responda a um link do YouTube ou texto.")
        return
    ydl = youtube_dl.YoutubeDL(
        {"outtmpl": "dls/%(title)s-%(id)s.%(ext)s", "format": "mp4", "noplaylist": True}
    )
    rege = re.match(
        r"http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?",
        url,
        re.M,
    )
    if not rege:
        yt = await extract_info(ydl, "ytsearch:" + url, download=False)
        yt = yt["entries"][0]
    else:
        yt = await extract_info(ydl, rege.group(), download=False)
    keyb = [
        [
            ("💿 Áudio", f'_aud.{yt["id"]}|{m.chat.id}|{user}'),
            ("🎬 Vídeo", f'_vid.{yt["id"]}|{m.chat.id}|{user}'),
        ],
    ]
    for f in yt["formats"]:
        if f["format_id"] == "140":
            fsize = f["filesize"] or 0
    if not fsize > 2147483648:
        if " - " in yt["title"]:
            performer, title = yt["title"].rsplit(" - ", 1)
        else:
            performer = yt.get("creator") or yt.get("uploader")
            title = yt["title"]
        text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n"
        text += f"💾 <code>{pretty_size(fsize)}</code> (min) | ⏳ <code>{datetime.timedelta(seconds=yt.get('duration'))}</code>"
        await m.reply_text(text, reply_markup=c.ikb(keyb))
    else:
        await m.reply_text("O arquivo é muito grande!")


@Client.on_callback_query(filters.regex("^(_(vid|aud))"))
async def cli_ytdl(c, cq: CallbackQuery):
    data, cid, userid = cq.data.split("|")
    if not cq.from_user.id == int(userid):
        return await cq.answer("Este botão não é para você!", cache_time=60)
    vid = re.sub(r"^\_(vid|aud)\.", "", data)
    url = "https://www.youtube.com/watch?v=" + vid
    edit = await cq.message.edit("Baixando...")
    if "vid" in data:
        ydl = youtube_dl.YoutubeDL(
            {
                "outtmpl": "dls/%(title)s-%(id)s.%(ext)s",
                "format": "mp4",
                "noplaylist": True,
            }
        )
    else:
        ydl = youtube_dl.YoutubeDL(
            {
                "outtmpl": "dls/%(title)s-%(id)s.%(ext)s",
                "format": "140",
                "noplaylist": True,
            }
        )
    yt = await extract_info(ydl, url, download=True)
    a = "Enviando..."
    await cq.message.edit(a)
    filename = ydl.prepare_filename(yt)
    ctime = time.time()
    r = await http.get(yt["thumbnail"])
    with open(f"{ctime}.png", "wb") as f:
        f.write(r.read())
    if "vid" in data:
        await c.send_chat_action(cid, "upload_video")
        await c.send_video(
            cid,
            filename,
            width=int(1920),
            height=int(1080),
            caption=yt["title"],
            duration=yt["duration"],
            thumb=f"{ctime}.png",
        )
    else:
        if " - " in yt["title"]:
            performer, title = yt["title"].rsplit(" - ", 1)
        else:
            performer = yt.get("creator") or yt.get("uploader")
            title = yt["title"]
        await c.send_chat_action(cid, "upload_audio")
        await c.send_audio(
            cid,
            filename,
            title=title,
            performer=performer,
            duration=yt["duration"],
            thumb=f"{ctime}.png",
        )
    os.remove(filename)
    os.remove(f"./{ctime}.png")
    await cq.message.edit("Feito!")


@Client.on_message(filters.cmd(command="tr", action="Google Tradutor.", group=GROUP))
async def translate(c: Client, m: Message):
    text = m.text[4:]
    lang = get_tr_lang(text)

    text = text.replace(lang, "", 1).strip() if text.startswith(lang) else text

    if m.reply_to_message and not text:
        text = m.reply_to_message.text or m.reply_to_message.caption

    if not text:
        return await m.reply_text(
            "<b>Uso:</b> <code>/tr &lt;idioma&gt; texto para tradução</code> (Também pode ser usado em resposta a uma mensagem)."
        )

    sent = await m.reply_text("Traduzindo...")
    langs = {}

    if len(lang.split("-")) > 1:
        langs["sourcelang"] = lang.split("-")[0]
        langs["targetlang"] = lang.split("-")[1]
    else:
        langs["targetlang"] = lang

    trres = await tr(text, **langs)
    text = trres.text

    res = html.escape(text)
    await sent.edit_text(
        (
            "<b>Idioma:</b> {from_lang} -> {to_lang}\n<b>Tradução:</b> <code>{translation}</code>"
        ).format(from_lang=trres.lang, to_lang=langs["targetlang"], translation=res)
    )
