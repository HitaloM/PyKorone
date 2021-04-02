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

import datetime
import random
import rapidjson as json

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.database import Chats, Users, XPs, Levels


LEVELS_GROUP = {}
with open("korone/levels_group.json", "r") as file:
    LEVELS_GROUP = json.loads(file.read())
    file.close()


LEVELS_GLOBAL = {}
with open("korone/levels_global.json", "r") as file:
    LEVELS_GLOBAL = json.loads(file.read())
    file.close()


@Client.on_message(filters.edited)
async def reject(c: Client, m: Message):
    m.stop_propagation()


@Client.on_message(~filters.private & filters.all, group=-10)
async def on_all_m(c: Client, m: Message):
    if not await Chats.filter(id=m.chat.id):
        await Chats.create(
            id=m.chat.id, title=m.chat.title, username=m.chat.username or ""
        )


@Client.on_message(~filters.private & filters.text, group=5)
async def on_text_m(c: Client, m: Message):
    length = len(m.text)
    now_date = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)

    user_db = (
        await Users.get_or_create(
            {
                "first_name": m.from_user.first_name,
                "last_name": m.from_user.last_name or "",
                "username": m.from_user.username or "",
                "last_update": now_date,
            },
            id=m.from_user.id,
        )
    )[0]
    xp_db = (
        await XPs.get_or_create({"value": 0}, chat_id=m.chat.id, user_id=m.from_user.id)
    )[0]
    level_db = (
        await Levels.get_or_create(
            {"value": 1}, chat_id=m.chat.id, user_id=m.from_user.id
        )
    )[0]

    if (now_date - user_db.last_update).seconds >= 10:
        user_db.update_from_dict({"last_update": now_date})
        await user_db.save()

        xp_won = 75 * length // 4096
        if xp_won < 1:
            xp_won = random.randint(1, 15)

        # Chat
        current_xp = xp_db.value + xp_won
        current_level = level_db.value
        next_level = current_level + 1

        if str(next_level) in LEVELS_GROUP.keys():
            next_level_xp = LEVELS_GROUP[str(next_level)]

            if current_xp >= next_level_xp:
                current_level += 1
                next_level = current_level + 1
                if str(next_level) in LEVELS_GROUP.keys():
                    next_level_xp = LEVELS_GROUP[str(next_level)]
                    if current_xp >= next_level_xp:
                        current_level += 1
                        next_level = current_level + 1
                        next_level_xp = LEVELS_GROUP[str(next_level)]

                    await m.reply_text(
                        f"Parabéns {m.from_user.mention()}! Você subiu para o nível <b>{current_level}</b> (grupo) <code>{current_xp}</code>/<code>{next_level_xp}</code>."
                    )
                else:
                    await m.reply_text(
                        f"Parabéns {m.from_user.mention()}! Você chegou ao último nível (até o momento) <code>{current_level}</code> (grupo)."
                    )
        else:
            return

        xp_db.update_from_dict({"value": current_xp})
        await xp_db.save()
        level_db.update_from_dict({"value": current_level})
        await level_db.save()

        # Global
        current_xp = user_db.xp + xp_won
        current_level = user_db.level
        next_level = current_level + 1

        if str(next_level) in LEVELS_GLOBAL.keys():
            next_level_xp = LEVELS_GLOBAL[str(next_level)]

            if current_xp >= next_level_xp:
                current_level += 1
                next_level = current_level + 1
                if str(next_level) in LEVELS_GLOBAL.keys():
                    next_level_xp = LEVELS_GLOBAL[str(next_level)]
                    await m.reply_text(
                        f"Parabéns {m.from_user.mention()}! Você subiu para o nível <b>{current_level}</b> (global) <code>{current_xp}</code>/<code>{next_level_xp}</code>."
                    )
                else:
                    await m.reply_text(
                        f"Parabéns {m.from_user.mention()}! Você chegou ao último nível (até o momento) <code>{current_level}</code> (global)."
                    )

        user_db.update_from_dict({"xp": current_xp, "level": current_level})
        await user_db.save()
