import html
from contextlib import suppress
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, TelegramObject
from stfu_tg import Template, UserLink

from sophie_bot.modules.legacy_modules.modules.feds import get_fed_by_id, get_fed_f
from sophie_bot.modules.legacy_modules.utils.language import get_strings
from sophie_bot.modules.legacy_modules.utils.restrictions import ban_user
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.services.db import db
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log


class FedBanMiddleware(BaseMiddleware):
    async def is_fbanned(self, message: Message) -> bool:
        if message.sender_chat:
            # should be channel/anon
            return False
        if message.chat.type not in {"group", "supergroup"}:
            return False
        if not message.from_user:
            return False

        user_id = message.from_user.id
        user_name = message.from_user.first_name
        chat_id = message.chat.id

        log.debug("Enforcing fban check on {} in {}".format(user_id, chat_id))

        if not (fed := await get_fed_f(message)):
            return False

        elif await is_user_admin(chat_id, user_id):
            return False

        feds_list = [fed["fed_id"]]

        if "subscribed" in fed:
            feds_list.extend(fed["subscribed"])

        if ban := await db.fed_bans.find_one({"fed_id": {"$in": feds_list}, "user_id": user_id}):

            strings = await get_strings(chat_id, "feds")

            # check whether banned fed_id is chat's fed id else
            # user is banned in sub fed
            if fed["fed_id"] == ban["fed_id"] and "origin_fed" not in ban:
                doc = Template(
                    strings["automatic_ban"],
                    user=UserLink(user_id, user_name),
                    fed_name=html.escape(fed["fed_name"], False),
                )
            else:
                s_fed = await get_fed_by_id(ban["fed_id"] if "origin_fed" not in ban else ban["origin_fed"])
                if s_fed is None:
                    raise SophieException("The user is banned in the subscribed fed, but I cannot find it.")

                doc = Template(
                    strings["automatic_ban_sfed"],
                    user=UserLink(user_id, user_name),
                    fed_name=s_fed["fed_name"],
                )

            if "reason" in ban:
                doc += Template(strings["automatic_ban_reason"], text=ban["reason"])

            if not await ban_user(chat_id, user_id):
                return True

            with suppress(TelegramBadRequest):
                await message.reply(str(doc))

            await db.fed_bans.update_one({"_id": ban["_id"]}, {"$addToSet": {"banned_chats": chat_id}})

            return True

        return False

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and await self.is_fbanned(event):
            return

        return await handler(event, data)
