# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

from datetime import datetime
from typing import Iterable

from pyrogram import filters
from pyrogram.types import Message

from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils import http

GROUP = "spacex"

COMMANDS_HELP[GROUP] = {
    "description": False,
    "commands": {},
    "help": True,
}


@Korone.on_message(
    filters.cmd(command=r"spacex$", action=r"Informações sobre a SpaceX.", group=GROUP)
)
async def spacex_wiki(c: Korone, m: Message):
    r = await http.get("https://api.spacexdata.com/v4/company")
    if r.status_code == 200:
        sx = r.json()
    else:
        await m.reply_text(f"<b>Erro!</b> <code>{r.status_code}</code>")
        return

    text = f"<u><b>{sx['name']}</b></u> 🚀"
    text += f"\n<b>Endereço:</b> {sx['headquarters']['address']}, {sx['headquarters']['city']}, {sx['headquarters']['state']}"
    text += f"\n<b>Fundador:</b> {sx['founder']}"
    text += f"\n<b>Fundada em:</b> {sx['founded']}"
    text += ("\n<b>Funcionários:</b> <code>{:,}</code>").format(sx["employees"])
    text += f"\n<b>Plataformas de testes:</b> <code>{sx['test_sites']}</code>"
    text += f"\n<b>Plataformas de lançamentos:</b> <code>{sx['launch_sites']}</code>"
    text += f"\n<b>Veículos de lançamento:</b> <code>{sx['vehicles']}</code>"
    text += ("\n<b>Avaliada em:</b> <code>${:,}</code>").format(sx["valuation"])
    text += f"\n<b>CEO:</b> {sx['ceo']}"
    text += f", <b>CTO:</b> {sx['cto']}"
    text += f", <b>COO:</b> {sx['coo']}"
    text += f", <b>CTO de Propulsão:</b> {sx['cto_propulsion']}"
    text += f"\n\n<b>Resumo:</b> {sx['summary']}"

    keyboard = [
        [
            ("Twitter", f"{sx['links']['twitter']}", "url"),
            ("Flickr", f"{sx['links']['flickr']}", "url"),
        ],
        [("Website", f"{sx['links']['website']}", "url")],
    ]

    await m.reply_text(
        text=text,
        reply_markup=c.ikb(keyboard),
        disable_web_page_preview=True,
    )


@Korone.on_message(
    filters.cmd(
        command=r"spacex (?P<args>.+)",
        action=r"Informações sobre lançamentos da SpaceX.",
        group=GROUP,
    )
)
async def spacex_launch(c: Korone, m: Message):
    arg = m.matches[0]["args"]

    args_list: Iterable[str] = ("latest", "next")

    if arg not in args_list:
        await m.reply_text(
            f"<code>{arg}</code> não é um argumento válido! "
            f"Argumentos disponíveis: <code>{', '.join(str(x) for x in args_list)}</code>."
        )
        return

    r = await http.get(f"https://api.spacexdata.com/v4/launches/{arg}")
    if r.status_code == 200:
        sx = r.json()
    else:
        await m.reply_text(f"<b>Erro!</b> <code>{r.status_code}</code>")
        return

    dt = datetime.utcfromtimestamp(sx["date_unix"]).strftime("%d-%m-%Y %H:%M:%S")
    images = sx["links"]["flickr"]["original"]

    res = await http.get(f"https://api.spacexdata.com/v4/rockets/{sx['rocket']}")
    rocket = res.json() if res.status_code == 200 else None
    res = await http.get(f"https://api.spacexdata.com/v4/launchpads/{sx['launchpad']}")
    launchpad = res.json() if res.status_code == 200 else None
    text = f"<b>Nome da missão:</b> {sx['name']}\n"
    text += f"<b>Voo Nº:</b> {sx['flight_number']}\n"
    if rocket:
        text += f"<b>Nome do foguete:</b> {rocket['name']}\n"
    if launchpad:
        text += f"<b>Palataforma de lançamento:</b> {launchpad['name']}\n"
    if sx["success"]:
        text += f"<b>Sucesso:</b> {sx['success']}\n"
    if sx["failures"]:
        text += f"<b>Falhas:</b> {sx['failures']}\n"
    text += f"<b>Data de lançamento:</b> <code>{dt}</code>\n\n"

    if sx["details"]:
        text += f"<b>Detalhes:</b>\n{sx['details']}"

    keyboard = None
    if sx["links"]["reddit"]["campaign"]:
        keyboard = [[("Reddit", sx["links"]["reddit"]["campaign"], "url")]]
        if sx["links"]["webcast"]:
            keyboard[0].append(("YouTube", sx["links"]["webcast"], "url"))
    elif sx["links"]["webcast"]:
        keyboard = [[("YouTube", sx["links"]["webcast"], "url")]]

    if keyboard:
        keyboard = c.ikb(keyboard)

    if images:
        await m.reply_photo(
            photo=images[0],
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await m.reply_text(
            text=text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
