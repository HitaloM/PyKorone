from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Chat, Message, TelegramObject, User

from sophie_bot import CONFIG
from sophie_bot.db.models import FiltersModel
from sophie_bot.modules.filters.utils_.handle_legacy import handle_legacy_filter
from sophie_bot.modules.filters.utils_.match_legacy import match_legacy_filter
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log


class EnforceFiltersMiddleware(BaseMiddleware):
    @staticmethod
    async def _is_to_drop(message: Message) -> bool:
        sender: Optional[User | Chat] = message.sender_chat or message.from_user

        if not sender:
            log.debug("EnforceFiltersMiddleware: no sender, dropping...")
            return True

        if message.chat.type not in {"group", "supergroup"}:
            log.debug("EnforceFiltersMiddleware: not a group, dropping...")
            return True

        # TODO: Other people send as channel / anon admins

        # OP
        # if sender_id in CONFIG.operators:
        #     log.debug('EnforceFiltersMiddleware: operator, dropping...')
        #     return True

        # Whatever the sender is an admin
        # TODO: Use fitler match of /delfilter handler here instead of hard-coding

        text = message.text
        chat_id = message.chat.id
        if text and len(text) > 5 and any(text.startswith(prefix) for prefix in CONFIG.commands_prefix):
            cmd_text = text[1:].split(" ", 1)[0]

            if cmd_text in {
                "filters",
                "listfilters",
                "delfilters",
                "delallfilters",
                "addfilter",
                "newfilter",
                "delfilter",
            } and await is_user_admin(chat_id, sender.id):
                log.debug("EnforceFiltersMiddleware: admin, dropping...")
                return True

        return False

    @staticmethod
    async def _handle_filters(message: Message):
        chat_id: int = message.chat.id

        all_filters = await FiltersModel.get_filters(chat_id)
        matched_filters: list[FiltersModel] = [fil for fil in all_filters if match_legacy_filter(message, fil.handler)]

        # We don't want to handle many times the same action, therefore, keep a log of previously handled actions
        triggered_actions: list[str] = []
        triggered = 0
        for matched_filter in matched_filters:
            if triggered >= CONFIG.filters_max_triggers:
                log.debug("EnforceFiltersMiddleware: triggered maximum number of filters, dropping...")
                break

            # TODO: Deal with modern filters
            if matched_filter.action and matched_filter.action in triggered_actions:
                log.debug("EnforceFiltersMiddleware: already triggered action, dropping...")
                continue

            if matched_filter.action:
                triggered_actions.append(matched_filter.action)
                await handle_legacy_filter(matched_filter, message)

            triggered += 1

        # If filter triggered - skip other handlers
        if triggered:
            raise SkipHandler

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        log.debug("EnforceFiltersMiddleware: checking filters...")

        if not isinstance(event, Message):
            raise SophieException("EnforceFiltersMiddleware: not a message")

        if await self._is_to_drop(event):
            log.debug("EnforceFiltersMiddleware: dropping...")
        else:
            await self._handle_filters(event)

        return await handler(event, data)
