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

from datetime import datetime
from typing import Dict, List

from pyrogram import filters
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.korone import Korone
from korone.utils import http

GROUP = "spacex"

COMMANDS_HELP[GROUP]: Dict = {
    "name": "SpaceX",
    "text": "Esse é meu módulo sobre a SpaceX.",
    "commands": {},
    "help": True,
}


@Korone.on_message(
    filters.cmd(command="spacex$", action="Informações sobre a SpaceX.", group=GROUP)
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
    text += f"\n<b>Funcionários:</b> <code>{sx['employees']}</code>"
    text += f"\n<b>Plataformas de testes:</b> <code>{sx['test_sites']}</code>"
    text += f"\n<b>Plataformas de lançamentos:</b> <code>{sx['launch_sites']}</code>"
    text += f"\n<b>Veículos de lançamento:</b> <code>{sx['vehicles']}</code>"
    text += f"\n<b>Avaliada em:</b> <code>{sx['valuation']}</code>"
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
        text, reply_markup=c.ikb(keyboard), disable_web_page_preview=True
    )


@Korone.on_message(
    filters.cmd(
        command="spacex (?P<args>.+)",
        action="Informações sobre lançamentos da SpaceX.",
        group=GROUP,
    )
)
async def spacex_launch(c: Korone, m: Message):
    args_list: Dict[List] = ["latest", "next"]
    arg = m.matches[0]["args"]

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

    rocket = None
    res = await http.get(f"https://api.spacexdata.com/v4/rockets/{sx['rocket']}")
    if res.status_code == 200:
        rocket = res.json()

    launchpad = None
    res = await http.get(f"https://api.spacexdata.com/v4/launchpads/{sx['launchpad']}")
    if res.status_code == 200:
        launchpad = res.json()

    text = f"<b>None da missão:</b> {sx['name']}\n"
    text += f"<b>Voo Nº:</b> {sx['flight_number']}\n"
    if rocket:
        text += f"<b>Nome do foguete:</b> {rocket['name']}\n"
    if launchpad:
        text += f"<b>Palataforma de lançamento:</b> {launchpad['name']}\n"
    if sx["success"]:
        text += f"<b>Sucesso:</b> {sx['success']}\n"
    if sx["failures"]:
        text += f"<b>Falhas:</b> {sx['failures']}\n"
    text += f"<b>Data de lançamento UTC:</b> <code>{dt}</code>\n\n"

    if images:
        for i, image in enumerate(images, start=1):
            text += f", <a href='{image}'>Flicker {i}</a>"

    if sx["details"]:
        text += f"<b>Detalhes:</b>\n{sx['details']}"

    keyboard = [[("Reddit", sx["links"]["reddit"]["campaign"], "url")]]

    if sx["links"]["webcast"]:
        keyboard[0].append(("YouTube", sx["links"]["webcast"], "url"))

    if images:
        await m.reply_photo(
            photo=images[0],
            caption=text,
            reply_markup=c.ikb(keyboard),
            disable_web_page_preview=True,
        )
    else:
        await m.reply_text(
            text=text,
            reply_markup=c.ikb(keyboard),
            disable_web_page_preview=True,
        )
