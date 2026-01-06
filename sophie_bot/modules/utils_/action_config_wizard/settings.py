from __future__ import annotations

from typing import Any

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from beanie import PydanticObjectId
from pymongo.errors import PyMongoError

from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.utils.i18n import gettext as _
from .base import ActionConfigSettingsHandlerABC
from .callbacks import ACWSettingCallback, ACWCoreCallback
from .fsm import ActionConfigFSM
from .helpers import _convert_action_data_to_model
from .service import ensure_session, set_action


class ActionConfigSettingsHandlerMixin(ActionConfigSettingsHandlerABC):
    """Mixin providing concrete implementation for the settings handler."""

    @staticmethod
    def create_filters(callback_prefix: str) -> tuple[CallbackType, ...]:
        """Create filters for this callback handler."""
        return (ACWSettingCallback.filter((F.mod == callback_prefix)),)

    async def handle(self) -> Any:
        """Handle settings button click."""
        callback_query: CallbackQuery = self.event
        data: ACWSettingCallback = self.data["callback_data"]

        parsed_action_name = data.name
        parsed_setting_id = data.setting

        if parsed_action_name not in ALL_MODERN_ACTIONS:
            await callback_query.answer(_("Invalid action"))
            return

        # Get chat ID from the callback query
        chat_tid: PydanticObjectId = self.connection.db_model.iid  # type: ignore

        # Ensure/refresh session and set action name for staging
        state = self.data.get("state")
        if not isinstance(state, FSMContext):
            await callback_query.answer(_("State management not available"))
            return
        await ensure_session(state, getattr(self, "module_name", ""), chat_tid)
        await set_action(state, parsed_action_name)

        # Get action and current data
        action = ALL_MODERN_ACTIONS[parsed_action_name]

        try:
            model = await self.get_model(chat_tid)
            actions = await self.get_actions(model)
            current_action_data = None
            for act in actions:
                if act.name == parsed_action_name:
                    current_action_data = act.data
                    break
        except PyMongoError:
            current_action_data = None

        # Get available settings
        settings = action.settings(_convert_action_data_to_model(action, current_action_data or {}))
        if parsed_setting_id not in settings:
            await callback_query.answer(_("Invalid setting"))
            return

        setting = settings[parsed_setting_id]

        # Check if setting has interactive setup
        if setting.setup_message and setting.setup_confirm:
            await self._start_setting_setup(callback_query, parsed_action_name, parsed_setting_id, chat_tid)
        else:
            await callback_query.answer(_("Setting configuration not available"))

    async def _start_setting_setup(
        self, callback_query: CallbackQuery, action_name: str, setting_id: str, chat_tid: PydanticObjectId
    ) -> None:
        """Start interactive setup process for a setting."""
        action = ALL_MODERN_ACTIONS[action_name]
        try:
            model = await self.get_model(chat_tid)
            actions = await self.get_actions(model)
            current_action_data = None
            for act in actions:
                if act.name == action_name:
                    current_action_data = act.data
                    break
        except PyMongoError:
            current_action_data = None
        settings = action.settings(_convert_action_data_to_model(action, current_action_data or {}))
        setting = settings[setting_id]

        # Store setup data in FSM
        state = self.data.get("state")
        if not isinstance(state, FSMContext):
            await callback_query.answer(_("State management not available"))
            return

        await state.update_data(
            setting_setup_action=action_name,
            setting_setup_setting_id=setting_id,
            setting_setup_chat_tid=str(chat_tid),
            setting_setup_callback_prefix=self.callback_prefix,
        )
        await state.set_state(ActionConfigFSM.interactive_setup)

        # Get and send setup message
        if not setting.setup_message:
            await callback_query.answer(_("Setting setup not properly configured"))
            return

        setup_message = await setting.setup_message(callback_query, self.data)

        # Add cancel button to setup message
        reply_markup = setup_message.reply_markup
        if not reply_markup:
            from aiogram.types import InlineKeyboardMarkup

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[])

        reply_markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=_("❌ Cancel"), callback_data=ACWCoreCallback(mod=self.callback_prefix, op="cancel").pack()
                )
            ]
        )

        if callback_query.message and isinstance(callback_query.message, Message):
            await callback_query.message.edit_text(setup_message.text, reply_markup=reply_markup)
