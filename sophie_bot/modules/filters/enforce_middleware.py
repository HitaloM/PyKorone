from functools import lru_cache
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, TelegramObject, User
from stfu_tg import Doc
from stfu_tg.doc import Element

from sophie_bot.config import CONFIG
from sophie_bot.db.models import FiltersModel
from sophie_bot.modules.filters.fsm import FilterEditFSM
from sophie_bot.modules.filters.utils_.handle_action import (
    handle_legacy_filter_action,
    handle_modern_filter_action,
)
from sophie_bot.modules.filters.utils_.match_legacy import match_legacy_handler
from sophie_bot.modules.help.utils.extract_info import get_all_cmds_raw
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.services.bot import bot
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import LazyProxy
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
    ) -> tuple[list[str], list[Element | str | LazyProxy]]:
        log.debug("EnforceFiltersMiddleware: handling modern actions...")

        triggered: list[str] = []
        messages = []

        # Inject filter ID into data for logging purposes
        data["filter_id"] = str(filter_item.id)

        for action, action_data in filter_item.actions.items():
            if action in triggered_actions:
                log.debug("EnforceFiltersMiddleware: already triggered action, dropping...")
                continue

            log.debug("EnforceFiltersMiddleware: handling action", action=action)

            action_message = await handle_modern_filter_action(message, action, data, action_data)
            if action_message:
                messages.append(action_message)
            triggered.append(action)

        return triggered, messages

    @staticmethod
    async def _handle_action_messages(message: Message, messages: list[Optional[Element | str | LazyProxy]]):
        doc = Doc(
            # Title(_("Filters 🪄")),
        )

        for msg in messages:
            doc += " "
            doc += msg

        async def send_message():
            return await bot.send_message(chat_id=message.chat.id, text=doc.to_html())

        await common_try(message.reply(doc.to_html()), reply_not_found=send_message)

    async def _process_filter(
        self, message: Message, data: dict[str, Any], matched_filter: FiltersModel, triggered_groups: list[str] = []
    ) -> tuple[list[str | None], list[Element | str | LazyProxy]]:
        if matched_filter.actions:
            return await self._handle_modern_action(matched_filter, triggered_groups, message, data)  # type: ignore
        elif matched_filter.action:
            return [await self._handle_legacy_action(matched_filter, triggered_groups, message)], []
        else:
            raise SophieException("EnforceFiltersMiddleware: no actions found")

    async def _process_filters(self, message: Message, data: dict[str, Any]):
        chat_id: int = message.chat.id

        all_filters = await FiltersModel.get_filters(chat_id)
        if not all_filters:
            return

        # Evaluate all filters asynchronously
        matched_filters: list[FiltersModel] = []
        for fil in all_filters:
            if await match_legacy_handler(message, fil.handler):
                matched_filters.append(fil)

        all_messages = []
        triggered_groups: list[str] = []  # Handled action groups, to stop same actions from repeating

        for idx, matched_filter in enumerate(matched_filters):
            if idx > CONFIG.filters_max_triggers:
                log.debug("EnforceFiltersMiddleware: triggered maximum number of filters, dropping...")
                break

            actions, messages = await self._process_filter(
                message, data, matched_filter, triggered_groups=triggered_groups
            )
            all_messages.extend(messages)
            triggered_groups.extend((action for action in actions if action))

        if all_messages:
            await self._handle_action_messages(message, all_messages)

        # If filter triggered - skip other handlers
        if matched_filters:
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

        await self._process_filters(event, data)

        return await handler(event, data)
