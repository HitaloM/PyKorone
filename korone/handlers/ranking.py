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

import rapidjson as json

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.database import Users, XPs, Levels


LEVELS_GROUP = {}
with open("korone/levels_group.json", "r") as file:
    LEVELS_GROUP = json.loads(file.read())
    file.close()


LEVELS_GLOBAL = {}
with open("korone/levels_global.json", "r") as file:
    LEVELS_GLOBAL = json.loads(file.read())
    file.close()


@Client.on_message(
    filters.cmd(command="ranking$", action="Ranking do grupo.") & filters.group
)
async def ranking(c: Client, m: Message):
    user_levels = sorted(
        await Levels.filter(chat_id=m.chat.id),
        key=lambda level: level.value,
        reverse=True,
    )

    text = f"Ranking de níveis de <b>{m.chat.title}</b>:"

    for index, level in enumerate(user_levels):
        if (index + 1) >= 50:
            break

        first_name = (await Users.get(id=level.user_id)).first_name

        current_xp = (await XPs.get(chat_id=m.chat.id, user_id=level.user_id)).value
        current_level = level.value
        next_level = current_level + 1
        next_level_xp = (
            LEVELS_GROUP[str(next_level)]
            if str(next_level) in LEVELS_GROUP.keys()
            else 0
        )

        text += f"\n    <i>#{index + 1}</i> {first_name} <b>{current_level}</b> (<code>{current_xp}</code>/<code>{next_level_xp}</code>)"

    await m.reply_text(text)


@Client.on_message(filters.cmd(command="ranking global$", action="Ranking global."))
async def ranking_global(c: Client, m: Message):
    users = sorted(await Users.all(), key=lambda user: user.level, reverse=True)

    text = f"Ranking de níveis <b>global</b>:"

    for index, user in enumerate(users):
        if (index + 1) >= 50:
            break

        first_name = user.first_name

        current_xp = user.xp
        current_level = user.level
        next_level = current_level + 1
        next_level_xp = (
            LEVELS_GLOBAL[str(next_level)]
            if str(next_level) in LEVELS_GLOBAL.keys()
            else 0
        )

        text += f"\n    <i>#{index + 1}</i> {first_name} <b>{current_level}</b> (<code>{current_xp}</code>/<code>{next_level_xp}</code>)"

    await m.reply_text(text)
