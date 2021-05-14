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

import asyncio
import time

from pyrogram.errors import BadRequest, FloodWait

from korone.utils import aiowrap


@aiowrap
def extract_info(instance, url, download=True):
    return instance.extract_info(url, download)


async def up_progress(current, total, c, m, action: str):
    last_edit = 3
    percent = current * 100 / total
    if last_edit + 1 < int(time.time()) or current == total:
        if action == "video":
            await c.send_chat_action(m.chat.id, "upload_video")
        if action == "audio":
            await c.send_chat_action(m.chat.id, "upload_audio")
        try:
            await m.edit("Enviando... <code>{:.1f}%</code>".format(percent))
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except BadRequest:
            pass
        finally:
            last_edit = int(time.time())


def down_progress(m, d):
    last_edit = 3
    if d["status"] == "finished":
        return
    if d["status"] == "downloading":
        if last_edit + 1 < int(time.time()):
            percent = d["_percent_str"]
            try:
                m.edit(f"Baixando... <code>{percent}</code>")
            except FloodWait as e:
                time.sleep(e.x)
            except BadRequest:
                pass
            finally:
                last_edit = int(time.time())
