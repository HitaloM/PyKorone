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


from config import SUDOERS
from database import Banneds, Chats
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest, ChatAdminRequired, UserAdminInvalid
from kantex.html import KanTeXDocument, Section, KeyValueItem, Bold, Code
from typing import List, Union


@Client.on_message(filters.cmd("gban$") & filters.reply & filters.user(SUDOERS))
async def on_gban_r_n_r_m(c: Client, m: Message):
    reply = m.reply_to_message
    user = reply.from_user
    field = str(user.id)
    await gban_user(c, m, field)


@Client.on_message(
    filters.cmd("gban (?P<reason>.+)") & filters.reply & filters.user(SUDOERS)
)
async def on_gban_r_m(c: Client, m: Message):
    reason = m.matches[0]["reason"]
    reply = m.reply_to_message
    user = reply.from_user
    field = str(user.id) + " " + reason
    await gban_user(c, m, field)


@Client.on_message(filters.cmd("gban (?P<field>.+)") & filters.user(SUDOERS))
async def on_gban_m(c: Client, m: Message):
    field = m.matches[0]["field"]
    await gban_user(c, m, field)


@Client.on_message(filters.cmd("ungban$") & filters.reply & filters.user(SUDOERS))
async def on_ungban_r_m(c: Client, m: Message):
    reply = m.reply_to_message
    user = reply.from_user.id
    await ungban_user(c, m, [user])


@Client.on_message(filters.cmd("ungban (?P<users>.+)") & filters.user(SUDOERS))
async def on_ungban_m(c: Client, m: Message):
    users = m.matches[0]["users"]
    users = users.split()
    await ungban_user(c, m, users)


async def gban_user(c: Client, m: Message, field: str):
    query = field.split()
    silent = False
    for item in query:
        if item == "-d":
            field = field.replace("-d ", "")
            silent = True
    if silent:
        try:
            await m.delete()
        except BaseException:
            pass
    else:
        sent = await m.reply_text("Initializing the global ban...")

    users = []
    chats_banned = []

    for item in query:
        if item.isdecimal():
            user = int(item)
            if item == c.me.id:
                continue
            field = field[len(item) + 1 :]
        elif not item.startswith("@"):
            break
        try:
            user = await c.get_users(item)
            if user:
                if user.id == c.me.id or user.id in SUDOERS:
                    continue
                users.append(str(user.id))
                if not item.isdecimal():
                    field = field[len(item) + 1 :]
            else:
                users.append(str(item))
        except BaseException:
            pass

    if m.chat.type != "private":
        async for member in c.iter_chat_members(chat_id=m.chat.id):
            if member.user.id in users:
                try:
                    if (
                        await c.kick_chat_member(
                            chat_id=m.chat.id, user_id=member.user.id
                        )
                        and m.chat.title not in chats_banned
                    ):
                        chats_banned.append(m.chat.title)
                except BadRequest:
                    pass
                except UserAdminInvalid:
                    pass
                except ChatAdminRequired:
                    pass

    for user in users:
        chats = await Chats.all()
        for chat in chats:
            try:
                if (
                    await c.kick_chat_member(chat_id=chat.id, user_id=user)
                    and chat.title not in chats_banned
                ):
                    chats_banned.append(chat.title)
            except BadRequest:
                pass
            except UserAdminInvalid:
                pass
            except ChatAdminRequired:
                pass

    reason = field
    if len(reason) < 1:
        reason = "spam[gban]"

    if chats_banned:
        chats_banned = len(chats_banned)
    else:
        if len(users) > 1:
            chats_banned = "I didn't see them or managed to ban them."
        else:
            chats_banned = "I didn't see him or managed to ban him."

    if len(users) < 1:
        doc = "Specify someone."
    elif len(users) > 0:
        for user in users:
            if not await Banneds.filter(id=user):
                await Banneds.create(
                    id=user, name=(await c.get_users(user)).first_name or ""
                )
        users = ", ".join(users)
        doc = KanTeXDocument(
            Section(
                Bold("GBanned Users"),
                KeyValueItem(Bold("Reason"), Code(reason)),
                KeyValueItem(Bold("IDs"), Code(users)),
                KeyValueItem(Bold("Chats banneds"), Code(chats_banned)),
            )
        )
    if not silent:
        await sent.edit_text(doc)


async def ungban_user(c: Client, m: Message, _users: List[Union[str, int]]):
    sent = await m.reply_text("Initializing the global unban...")

    chats_unbanned = []
    users = []

    for user in _users:
        user = str(user)
        if user.isdecimal():
            user = int(user)
            if user == c.me.id:
                continue
        elif not user.startswith("@"):
            break
        try:
            user = await c.get_users(user)
            if user:
                if user.id == c.me.id or user.id in SUDOERS:
                    continue
                users.append(str(user.id))
            else:
                users.append(str(user))
        except BaseException:
            pass

    if m.chat.type != "private":
        async for member in c.iter_chat_members(chat_id=m.chat.id):
            if member.user.id in users:
                try:
                    if (
                        await c.unban_chat_member(
                            chat_id=m.chat.id, user_id=member.user.id
                        )
                        and m.chat.title not in chats_unbanned
                    ):
                        chats_unbanned.append(m.chat.title)
                except BadRequest:
                    pass
                except UserAdminInvalid:
                    pass
                except ChatAdminRequired:
                    pass

    for user in users:
        chats = await Chats.all()
        for chat in chats:
            try:
                if (
                    await c.unban_chat_member(chat_id=chat.id, user_id=user)
                    and chat.title not in chats_unbanned
                ):
                    chats_unbanned.append(chat.title)
            except BadRequest:
                pass
            except UserAdminInvalid:
                pass
            except ChatAdminRequired:
                pass

    if chats_unbanned:
        chats_unbanned = len(chats_unbanned)
    else:
        if len(users) > 1:
            chats_unbanned = "I didn't see them or managed to unban them."
        else:
            chats_unbanned = "I didn't see him or managed to unban him."

    if len(users) < 1:
        doc = "Specify someone."
    elif len(users) > 0:
        for user in users:
            if await Banneds.filter(id=user):
                await Banneds.filter(id=user).delete()
        users = ", ".join(users)
        doc = KanTeXDocument(
            Section(
                Bold("un-GBanned Users"),
                KeyValueItem(Bold("IDs"), Code(users)),
                KeyValueItem(Bold("Chats unbanneds"), Code(chats_unbanned)),
            )
        )
    await sent.edit_text(doc)
