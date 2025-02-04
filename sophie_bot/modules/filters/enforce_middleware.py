from functools import lru_cache
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, TelegramObject, User

from sophie_bot import CONFIG
from sophie_bot.db.models import FiltersModel
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.utils_.handle_action import (
    handle_legacy_filter_action,
    handle_modern_filter_action,
)
from sophie_bot.modules.filters.utils_.match_legacy import match_legacy_handler
from sophie_bot.modules.help.utils.extract_info import get_all_cmds_raw
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log


class EnforceFiltersMiddleware(BaseMiddleware):

    @staticmethod
    @lru_cache()
    def _get_all_cmds() -> tuple[str, ...]:
        return get_all_cmds_raw()

    async def _is_to_drop(self, message: Message, state: Optional[FSMContext]) -> bool:
        sender: Optional[User | Chat] = message.sender_chat or message.from_user

        if not sender:
            log.debug("EnforceFiltersMiddleware: no sender, dropping...")
            return True

        if message.chat.type not in {"group", "supergroup"}:
            log.debug("EnforceFiltersMiddleware: not a group, dropping...")
            return True

        # TODO: Other people send as channel / anon admins

        # Check for the filter setup states
        if state and FilterEditFSM.__name__ in (await state.get_state() or ""):
            log.debug("EnforceFiltersMiddleware: filter setup state, dropping...")
            return True

        # Check for the commands
        # This code is a little bit shit but honestly I don't see any other way to do it
        # Outer middlewares runs BEFORE filters, so we cannot access the CMDFilter,
        # therefore, we can't get the command object reliably
        # parsing it here is the only way
        text = message.text
        chat_id = message.chat.id
        if text and len(text) > 3 and any(text.startswith(prefix) for prefix in CONFIG.commands_prefix):
            cmd_text = text[1:].lower().split(" ", 1)[0]

            if cmd_text in self._get_all_cmds() and await is_user_admin(chat_id, sender.id):
                log.debug("EnforceFiltersMiddleware: admin and command, dropping...")
                return True

        return False

    @staticmethod
    async def _handle_legacy_action(
        filter_item: FiltersModel, triggered_actions: list[str], message: Message
    ) -> Optional[str]:
        log.debug("EnforceFiltersMiddleware: handling legacy action...")

        if filter_item.action and filter_item.action in triggered_actions:
            log.debug("EnforceFiltersMiddleware: already triggered action, dropping...")
            return None

        if filter_item.action:
            await handle_legacy_filter_action(filter_item, message)
            return filter_item.action

        return None

    @staticmethod
    async def _handle_modern_action(
        filter_item: FiltersModel, triggered_actions: list[str], message: Message, data: dict[str, Any]
    ) -> list[str]:
        log.debug("EnforceFiltersMiddleware: handling modern actions...")

        triggered: list[str] = []

        for action, action_data in filter_item.actions.items():

            if action in triggered_actions:
                log.debug("EnforceFiltersMiddleware: already triggered action, dropping...")
                continue

            log.debug("EnforceFiltersMiddleware: handling action", action=action)

            await handle_modern_filter_action(message, action, data, action_data)
            triggered.append(action)

        return triggered

    async def _handle_filters(self, message: Message, data: dict[str, Any]):
        chat_id: int = message.chat.id

        all_filters = await FiltersModel.get_filters(chat_id)
        matched_filters: list[FiltersModel] = [fil for fil in all_filters if match_legacy_handler(message, fil.handler)]

        # We don't want to handle many times the same action, therefore, keep a log of previously handled actions
        triggered_actions: list[str] = []  # TODO: Rather try to group filter actions
        triggered = 0
        for matched_filter in matched_filters:
            if triggered > CONFIG.filters_max_triggers:
                log.debug("EnforceFiltersMiddleware: triggered maximum number of filters, dropping...")
                break

            # Handler filter actions
            if matched_filter.actions:
                # Modern
                triggered_actions.extend(
                    await self._handle_modern_action(matched_filter, triggered_actions, message, data)
                )
            elif matched_filter.action:
                # Legacy
                if action := await self._handle_legacy_action(matched_filter, triggered_actions, message):
                    triggered_actions.append(action)
            else:
                raise SophieException("EnforceFiltersMiddleware: no actions found")

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

        if await self._is_to_drop(event, data.get("state")):
            log.debug("EnforceFiltersMiddleware: dropping...")
            return await handler(event, data)

        await self._handle_filters(event, data)

        return await handler(event, data)
