# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import datetime
import html
import io
import os
import re
import shutil
import tempfile
from typing import Union

from bs4 import BeautifulSoup as bs
from httpx._exceptions import TimeoutException
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.errors import BadRequest, Forbidden, MessageTooLong
from pyrogram.types import CallbackQuery, Message
from telegraph.aio import Telegraph
from telegraph.exceptions import TelegraphException
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from korone.bot import Korone
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.image import stickcolorsync
from korone.handlers.utils.misc import escape_definition
from korone.handlers.utils.translator import get_tr_lang, tr
from korone.handlers.utils.ytdl import extract_info
from korone.utils import http, pretty_size

GROUP = "utils"

COMMANDS_HELP[GROUP] = {
    "name": "Utilidades",
    "text": "Este é meu módulo de comandos utilitários.",
    "commands": {},
    "help": True,
}

tg = Telegraph()


@Korone.on_message(
    filters.cmd(
        command="pypi (?P<search>.+)",
        action="Pesquisa de módulos no PyPI.",
        group=GROUP,
    )
)
async def pypi(c: Korone, m: Message):
    text = m.matches[0]["search"]
    r = await http.get(f"https://pypi.org/pypi/{text}/json")
    if r.status_code == 200:
        json = r.json()
        pypi_info = escape_definition(json["info"])
        message = (
            "<b>%s</b> por <i>%s %s</i>\n"
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
        keyboard = None
        if pypi_info["home_page"] and pypi_info["home_page"] != "UNKNOWN":
            keyboard = c.ikb(
                [[("Página inicial do pacote", pypi_info["home_page"], "url")]]
            )
        await m.reply_text(
            message,
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
    else:
        await m.reply_text(
            f"Não consegui encontrar <b>{text}</b> no PyPi (<b>Error:</b> <code>{r.status_code}</code>)",
            disable_web_page_preview=True,
        )
    return


@Korone.on_message(
    filters.cmd(
        command="cleanup",
        action="Banir contas excluídas do grupo.",
        group=GROUP,
    )
)
async def cleanup(c: Korone, m: Message):
    if m.chat.type == ChatType.PRIVATE:
        await m.reply_text("Este comando é para ser usado em grupos!")
        return

    member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)
    if member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        deleted = []
        sent = await m.reply_text("Iniciando limpeza...")
        async for t in c.get_chat_members(chat_id=m.chat.id):
            if t.user.is_deleted:
                try:
                    await c.ban_chat_member(m.chat.id, t.user.id)
                    await m.chat.unban_member(t.user.id)
                    deleted.append(t)
                except BadRequest:
                    pass
                except Forbidden as e:
                    await m.reply_text(
                        f"Eu estou impedido de executar este comando! >-<\n<b>Erro:</b> <code>{e}</code>"
                    )
                    return
        if deleted:
            await sent.edit_text(
                f"Removi todas as {len(deleted)} contas excluídas do grupo!"
            )
        else:
            await sent.edit_text("Não há contas excluídas no grupo!")
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")


@Korone.on_message(
    filters.cmd(
        command="stickers (?P<search>.+)",
        action="Pesquise stickers.",
        group=GROUP,
    )
)
async def cb_sticker(c: Korone, m: Message):
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


@Korone.on_message(
    filters.cmd(
        command="color (?P<hex>.+)",
        action="Obtenha uma cor em sticker através do hex ou nome.",
        group=GROUP,
    )
)
async def stickcolor(c: Korone, m: Message):
    args = m.matches[0]["hex"]
    color_sticker = await stickcolorsync(args)

    if color_sticker:
        await m.reply_sticker(color_sticker)
    else:
        await m.reply_text(
            f"<code>{args}</code> é uma cor inválida, use <code>#hex</code> ou o nome da cor."
        )


@Korone.on_message(
    filters.cmd(
        command=r"ttdl(\s(?P<text>.+))?",
        action="Faça o Korone baixar um vídeo do Twitter e enviar no chat atual.",
        group=GROUP,
    )
)
async def on_ttdl(c: Korone, m: Message):
    args = m.matches[0]["text"]

    if m.reply_to_message and m.reply_to_message.text:
        url = m.reply_to_message.text
    elif m.text and args:
        url = args
    else:
        await m.reply_text("Por favor, responda a um link de um vídeo do Twitter.")
        return

    rege = re.match(
        r"https?://(?:(?:www|m(?:obile)?)\.)?twitter\.com/(?:(?:i/web|[^/]+)/status|statuses)/(?P<id>\d+)",
        url,
        re.M,
    )
    if not rege:
        await m.reply_text("Isso não é um link válido!")
        return

    sent = await m.reply_text("Baixando...")

    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "ttdl")

    tdl = YoutubeDL(
        {
            "outtmpl": f"{path}/{m.from_user.id}-%(id)s.%(ext)s",
            "format": "mp4",
        }
    )
    tt = await extract_info(tdl, rege.group(), download=False)

    for f in tt["formats"]:
        if f["ext"] == "mp4":
            try:
                vwidth = f["width"]
                vheight = f["height"]
            except KeyError:
                pass
            vformat = f["format_id"]
            vheaders = f["http_headers"]

    tdl = YoutubeDL(
        {
            "outtmpl": f"{path}/{m.from_user.id}-%(id)s.%(ext)s",
            "format": vformat,
        }
    )

    try:
        tt = await extract_info(tdl, url, download=True)
    except BaseException as e:
        await sent.edit(f"<b>Error!</b>\n<code>{e}</code>")
        return

    filename = tdl.prepare_filename(tt)
    thumb = io.BytesIO((await http.get(tt["thumbnail"], headers=vheaders)).content)
    thumb.name = "thumbnail.jpeg"
    await sent.edit("Enviando...")
    keyboard = [[("🔗 Tweet", tt["webpage_url"], "url")]]
    await c.send_chat_action(m.chat.id, ChatAction.UPLOAD_VIDEO)
    try:
        if tt["duration"] and vwidth and vheight:
            await m.reply_video(
                video=filename,
                thumb=thumb,
                duration=int(tt["duration"]),
                width=int(vwidth),
                height=int(vheight),
                reply_markup=c.ikb(keyboard),
            )
        else:
            await m.reply_video(
                video=filename,
                thumb=thumb,
                reply_markup=c.ikb(keyboard),
            )
    except BadRequest as e:
        await m.reply_text(
            text=(
                "Desculpe! Não consegui enviar o "
                "vídeo por causa de um erro.\n"
                f"<b>Erro:</b> <code>{e}</code>"
            )
        )
    else:
        await sent.delete()
    shutil.rmtree(tempdir, ignore_errors=True)


@Korone.on_message(
    filters.cmd(
        command=r"ytdl(\s(?P<text>.+))?",
        action="Faça o Korone baixar um vídeo do YouTube e enviar no chat atual.",
        group=GROUP,
    )
)
async def on_ytdl(c: Korone, m: Message):
    YOUTUBE_REGEX = re.compile(
        r"(?m)http(?:s?):\/\/(?:www\.)?(?:music\.)?youtu(?:be\.com\/(watch\?v=|shorts/)|\.be\/|)([\w\-\_]*)(&(amp;)?[\w\?=]*)?"
    )
    PLAYLIST_REGEX = re.compile(rf".*({YOUTUBE_REGEX}\/|list=)([^#\&\?]*).*")
    TIME_REGEX = re.compile(r"[?&]t=([0-9]+)")
    args = m.matches[0]["text"]
    user = m.from_user.id

    if m.reply_to_message and m.reply_to_message.text:
        url = m.reply_to_message.text
    elif m.text and args:
        url = args
    else:
        await m.reply_text("Por favor, responda a um link do YouTube ou texto.")
        return

    ydl = YoutubeDL(
        {
            "outtmpl": "dls/%(title)s-%(id)s.%(ext)s",
            "format": "mp4",
            "noplaylist": True,
        }
    )
    match = YOUTUBE_REGEX.match(url)
    playlist = PLAYLIST_REGEX.match(url)

    if playlist:
        await m.reply_text("Playlists não são suportadas no momento!")
        return

    t = TIME_REGEX.search(url)
    temp = t.group(1) if t else 0
    if match:
        yt = await extract_info(ydl, match.group(), download=False)
    else:
        yt = await extract_info(ydl, "ytsearch:" + url, download=False)
        yt = yt["entries"][0]

    for f in yt["formats"]:
        if f["format_id"] == "140":
            afsize = f["filesize"] or 0
        if f["ext"] == "mp4" and f["filesize"]:
            vfsize = f["filesize"] or 0
            vformat = f["format_id"]

    keyboard = [
        [
            (
                "💿 Áudio",
                f"_aud.{yt['id']}|{afsize}|{vformat}|{temp}|{user}|{m.id}",
            ),
            (
                "🎬 Vídeo",
                f"_vid.{yt['id']}|{vfsize}|{vformat}|{temp}|{user}|{m.id}",
            ),
        ]
    ]

    if " - " in yt["title"]:
        performer, title = yt["title"].rsplit(" - ", 1)
    else:
        performer = yt.get("creator") or yt.get("uploader")
        title = yt["title"]

    text = f"🎧 <b>{performer}</b> - <i>{title}</i>\n"
    text += f"💾 <code>{pretty_size(afsize)}</code> (áudio) / <code>{pretty_size(int(vfsize))}</code> (vídeo)\n"
    text += f"⏳ <code>{datetime.timedelta(seconds=yt.get('duration'))}</code>"

    await m.reply_text(text, reply_markup=c.ikb(keyboard))


@Korone.on_callback_query(filters.regex("^(_(vid|aud))"))
async def cli_ytdl(c, cq: CallbackQuery):
    data, fsize, vformat, temp, userid, mid = cq.data.split("|")
    if cq.from_user.id != int(userid):
        return await cq.answer("Este botão não é para você!", cache_time=60)
    if int(fsize) > 209715200:
        return await cq.answer(
            (
                "Desculpe! Não posso baixar esta mídia pois ela "
                "ultrapassa o meu limite de 200MB de download."
            ),
            show_alert=True,
            cache_time=60,
        )
    vid = re.sub(r"^\_(vid|aud)\.", "", data)
    url = "https://www.youtube.com/watch?v=" + vid
    await cq.message.edit("Baixando...")
    await cq.answer("Seu pedido é uma ordem... >-<", cache_time=0)
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "ytdl")
    if "vid" in data:
        ydl = YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": f"{vformat}+140",
                "noplaylist": True,
            }
        )
    else:
        ydl = YoutubeDL(
            {
                "outtmpl": f"{path}/%(title)s-%(id)s.%(ext)s",
                "format": "140",
                "extractaudio": True,
                "noplaylist": True,
            }
        )
    try:
        yt = await extract_info(ydl, url, download=True)
    except DownloadError as e:
        await cq.message.edit(f"<b>Error!</b>\n<code>{e}</code>")
        return
    await cq.message.edit("Enviando...")
    filename = ydl.prepare_filename(yt)
    ttemp = f"⏰ {datetime.timedelta(seconds=int(temp))} | " if int(temp) else ""
    thumb = io.BytesIO((await http.get(yt["thumbnail"])).content)
    thumb.name = "thumbnail.jpeg"
    caption = f"{ttemp} <a href='{yt['webpage_url']}'>{yt['title']}</a></b>"
    if yt["view_count"]:
        caption += "\n<b>Views:</b> <code>{:,}</code>".format(yt["view_count"])
    if yt["like_count"]:
        caption += "\n<b>Likes:</b> <code>{:,}</code>".format(yt["like_count"])
    try:
        if "vid" in data:
            await c.send_chat_action(cq.message.chat.id, ChatAction.UPLOAD_VIDEO)
            await c.send_video(
                chat_id=cq.message.chat.id,
                video=filename,
                width=1920,
                height=1080,
                caption=caption,
                duration=yt["duration"],
                thumb=thumb,
                reply_to_message_id=int(mid),
            )
        else:
            if " - " in yt["title"]:
                performer, title = yt["title"].rsplit(" - ", 1)
            else:
                performer = yt.get("creator") or yt.get("uploader")
                title = yt["title"]

            await c.send_chat_action(cq.message.chat.id, ChatAction.UPLOAD_AUDIO)
            await c.send_audio(
                chat_id=cq.message.chat.id,
                audio=filename,
                caption=caption,
                title=title,
                performer=performer,
                duration=yt["duration"],
                thumb=thumb,
                reply_to_message_id=int(mid),
            )
    except BadRequest as e:
        await c.send_message(
            chat_id=cq.message.chat.id,
            text=(
                "Desculpe! Não consegui enviar o "
                "arquivo por causa de um erro.\n"
                f"<b>Erro:</b> <code>{e}</code>"
            ),
            reply_to_message_id=int(mid),
        )
    else:
        await cq.message.delete()

    shutil.rmtree(tempdir, ignore_errors=True)


@Korone.on_message(
    filters.cmd(
        command="tr",
        action="Use o Google Tradutor para traduzir textos.",
        group=GROUP,
    )
)
async def translate(c: Korone, m: Message):
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

    if len(text) == 4096:
        await sent.edit_text("Essa mensagem é muito grande para ser traduzida.")
        return

    langs = {}
    if len(lang.split("-")) > 1:
        langs["sourcelang"] = lang.split("-")[0]
        langs["targetlang"] = lang.split("-")[1]
    else:
        langs["targetlang"] = lang

    trres = await tr(text, **langs)
    text = trres.text

    res = html.escape(text)
    try:
        await sent.edit_text(
            (
                "<b>Idioma:</b> {from_lang} -> {to_lang}\n<b>Tradução:</b> <code>{translation}</code>"
            ).format(
                from_lang=trres.lang,
                to_lang=langs["targetlang"],
                translation=res,
            )
        )
    except MessageTooLong:
        await sent.edit_text("Essa mensagem é muito grande para ser traduzida.")


@Korone.on_message(
    filters.cmd(
        command="mcserver (?P<ip>.+)",
        action="Veja algumas informações de servidores de Minecraft Java Edition.",
        group=GROUP,
    )
)
@Korone.on_callback_query(filters.regex("^mcserver_(?P<ip>.+)"))
async def mcserver(c: Korone, m: Union[Message, CallbackQuery]):
    args = m.matches[0]["ip"]
    time = datetime.datetime.now()

    if isinstance(m, CallbackQuery):
        reply = m.message
    else:
        reply = await m.reply_text("Obtendo informações...")

    try:
        r = await http.get(f"https://api.mcsrvstat.us/2/{args}")
    except TimeoutException:
        await reply.edit("Desculpe, não consegui me conectar a API!")
        return

    if r.status_code in [500, 504, 505]:
        await reply.edit("A API está indisponível ou com instabilidade!")
        return

    keyboard = [[("🔄️ Atualizar", f"mcserver_{args}")]]
    a = r.json()
    if a["online"]:
        text = "<b>Minecraft Server:</b>"
        text += f"\n<b>IP:</b> {a['hostname'] if 'hostname' in a else a['ip']} (<code>{a['ip']}</code>)"
        text += f"\n<b>Port:</b> <code>{a['port']}</code>"
        text += f"\n<b>Online:</b> <code>{a['online']}</code>"
        text += f"\n<b>Mods:</b> <code>{len(a['mods']['names']) if 'mods' in a else 'N/A'}</code>"
        text += f"\n<b>Players:</b> <code>{a['players']['online']}/{a['players']['max']}</code>"
        if "list" in a["players"]:
            text += "\n<b>Players list:</b> {}".format(
                ", ".join(
                    f"<a href='https://namemc.com/profile/{name}'>{name}</a>"
                    for name in a["players"]["list"]
                )
            )

        text += f"\n<b>Version:</b> <code>{a['version']}</code>"
        try:
            text += f"\n<b>Software:</b> <code>{a['software']}</code>"
        except KeyError:
            pass
        text += f"\n<b>MOTD:</b> <i>{a['motd']['clean'][0]}</i>"
        text += f"\n\n<b>UPDATED:</b> <i>{time.strftime('%d/%m/%Y %H:%M:%S')}</i>"

    elif not a["ip"] or a["ip"] == "127.0.0.1":
        return await reply.edit("Isso não é um IP/domínio válido!")

    else:
        text = (
            "<b>Minecraft Server</b>:"
            f"\n<b>IP:</b> {a['hostname'] if 'hostname' in a else a['ip']} (<code>{a['ip']}</code>)"
            f"\n<b>Port:</b> <code>{a['port']}</code>"
            f"\n<b>Online:</b> <code>{a['online']}</code>"
            f"\n\n<b>UPDATED:</b> <i>{time.strftime('%d/%m/%Y %H:%M:%S')}</i>"
        )
    await reply.edit_text(
        text, disable_web_page_preview=True, reply_markup=c.ikb(keyboard)
    )


@Korone.on_message(
    filters.cmd(
        command="del$",
        action="Faça o Korone apagar uma mensagem.",
        group=GROUP,
    )
)
async def del_message(c: Korone, m: Message):
    if m.chat.type != ChatType.PRIVATE:
        member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)

    if m.chat.type == ChatType.PRIVATE or member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        try:
            if m.reply_to_message:
                await c.delete_messages(
                    chat_id=m.chat.id,
                    message_ids=[m.reply_to_message.id, m.id],
                    revoke=True,
                )
        except Forbidden as e:
            await m.reply_text(
                f"Eu estou impedido de executar este comando! >-<\n<b>Erro:</b> <code>{e}</code>"
            )
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")


@Korone.on_message(
    filters.cmd(
        command="telegraph",
        action="Envie textos ou mídias para o telegra.ph.",
        group=GROUP,
    )
)
async def telegraph(c: Korone, m: Message):

    if not m.reply_to_message:
        await m.reply_text("Por favor, responda a uma foto, vídeo, gif ou texto.")
        return

    await tg.create_account(
        short_name="PyKorone",
        author_name="PyKorone",
        author_url="https://t.me/PyKoroneBot",
    )

    if (
        m.reply_to_message.photo
        or m.reply_to_message.video
        or m.reply_to_message.animation
    ):
        file = await m.reply_to_message.download()
        try:
            r = await tg.upload_file(file)
        except TelegraphException as err:
            await m.reply_text(f"<b>Erro!</b> <code>{err}</code>")
            os.remove(file)
            return
        await m.reply_text(f"https://telegra.ph{r[0]['src']}")
    elif m.reply_to_message.text:
        r = await tg.create_page(
            "Auto generated by @PyKoroneBot",
            html_content=m.reply_to_message.text.html,
        )
        await m.reply_text(r["url"])
