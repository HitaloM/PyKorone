import html
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from stfu_tg import Template, UserLink

from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.legacy_modules.utils.language import get_strings
from sophie_bot.modules.legacy_modules.utils.restrictions import ban_user
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.modules.utils_.common_try import common_try
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

        # Get federation for this chat
        federation = await FederationService.get_federation_for_chat(chat_id)
        if not federation:
            return False

        # Skip check for admins
        if await is_user_admin(chat_id, user_id):
            return False

        # Check if user is banned in this federation or subscription chain
        ban_info = await FederationService.is_user_banned_in_chain(federation.fed_id, user_id)
        if not ban_info:
            return False

        ban, banning_fed = ban_info

        strings = await get_strings(chat_id, "feds")

        # Determine which federation actually banned the user
        if banning_fed.fed_id == federation.fed_id:
            # Banned in this federation
            doc = Template(
                strings["automatic_ban"],
                user=UserLink(user_id, user_name),
                fed_name=html.escape(federation.fed_name, False),
            )
        else:
            # Banned in a subscribed federation
            doc = Template(
                strings["automatic_ban_sfed"],
                user=UserLink(user_id, user_name),
                fed_name=html.escape(banning_fed.fed_name, False),
            )

        if ban.reason:
            doc += Template(strings["automatic_ban_reason"], text=ban.reason)

        if not await ban_user(chat_id, user_id):
            return True

        await common_try(message.reply(str(doc)))

        # Update banned_chats list
        if not ban.banned_chats:
            ban.banned_chats = []
        if chat_id not in ban.banned_chats:
            ban.banned_chats.append(chat_id)
            await ban.save()

        return True

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and await self.is_fbanned(event):
            return

        return await handler(event, data)
