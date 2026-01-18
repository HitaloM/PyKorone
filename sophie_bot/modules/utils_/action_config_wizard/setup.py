from __future__ import annotations

from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from beanie import PydanticObjectId
from bson.errors import InvalidId

from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupTryAgainException,
)
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.utils.i18n import gettext as _

from .base import ActionConfigSetupHandlerABC
from .fsm import ActionConfigFSM
from .helpers import _convert_action_data_to_model, _show_action_configured_message
from .service import is_active, set_action_data


class ActionConfigSetupHandlerMixin(ActionConfigSetupHandlerABC):
    """Mixin providing concrete implementation for the setup handler."""

    @staticmethod
    def create_filters():
        """Create filters for this message handler."""
        return (ActionConfigFSM.interactive_setup,)

    async def handle(self) -> Any:
        """Handle user input during interactive setup."""
        message: Message = self.event
        state = self.data.get("state")

        if not isinstance(state, FSMContext):
            return

        state_data = await state.get_data()

        # Determine chat ID for this session and validate TTL/context
        chat_tid_raw = state_data.get("action_setup_chat_tid") or state_data.get("setting_setup_chat_tid")
        module_name = getattr(self, "module_name", "")
        if chat_tid_raw and module_name:
            try:
                chat_iid = PydanticObjectId(chat_tid_raw)
            except (InvalidId, TypeError):
                chat_iid = None
            if chat_iid:
                active = await is_active(state, module_name, chat_iid)
                if not active:
                    await message.reply(_("Setup session expired. Please start again."))
                    await state.clear()
                    return

        # Check if this is action setup or setting setup
        if "setting_setup_action" in state_data:
            await self._handle_setting_setup(message, state, state_data)
        else:
            await self._handle_action_setup(message, state, state_data)

    async def _handle_action_setup(self, message: Message, state: FSMContext, state_data: dict) -> None:
        """Handle regular action interactive setup."""
        action_name = state_data.get("action_setup_name")
        chat_tid_raw = state_data.get("action_setup_chat_tid")

        if not action_name or not chat_tid_raw:
            await message.reply(_("Setup data not found. Please try again."))
            await state.clear()
            return

        try:
            chat_iid = PydanticObjectId(chat_tid_raw)
        except (InvalidId, TypeError):
            await message.reply(_("Invalid chat context. Please restart the setup."))
            await state.clear()
            return

        action = ALL_MODERN_ACTIONS.get(action_name)
        if not action or not action.interactive_setup or not action.interactive_setup.setup_confirm:
            await message.reply(_("Invalid action configuration."))
            await state.clear()
            return

        try:
            # Call the action's setup_confirm function
            action_data = await action.interactive_setup.setup_confirm(message, self.data)

            # Convert Pydantic model to dictionary if needed
            if hasattr(action_data, "model_dump"):
                action_data_dict = action_data.model_dump(mode="json")
            else:
                action_data_dict = action_data

            # Stage the new action (immutable until Done)
            from .controller import WizardController

            await WizardController.stage_action(
                state,
                getattr(self, "module_name", ""),
                chat_iid,
                action_name,
                action_data_dict,
            )

            # Show configured action with settings buttons (hide Delete/Cancel for new)
            callback_prefix = state_data.get("action_setup_callback_prefix", self.callback_prefix)

            await _show_action_configured_message(
                message,
                action_name,
                chat_iid,
                callback_prefix,
                self.success_message,
                action_data_dict,
                show_delete=False,
                show_cancel=False,
            )
            # Exit interactive setup state but keep staged data
            await state.set_state(None)

        except ActionSetupTryAgainException:
            # Let user try again - don't clear state
            pass

    async def _handle_setting_setup(self, message: Message, state: FSMContext, state_data: dict) -> None:
        """Handle setting interactive setup."""
        action_name = state_data.get("setting_setup_action")
        setting_id = state_data.get("setting_setup_setting_id")
        chat_tid_raw = state_data.get("setting_setup_chat_tid")

        if not action_name or not setting_id or not chat_tid_raw:
            await message.reply(_("Setup data not found. Please try again."))
            await state.clear()
            return

        try:
            chat_iid = PydanticObjectId(chat_tid_raw)
        except (InvalidId, TypeError):
            await message.reply(_("Invalid chat context. Please restart the setup."))
            await state.clear()
            return

        action = ALL_MODERN_ACTIONS.get(action_name)
        if not action:
            await message.reply(_("Invalid action."))
            await state.clear()
            return

        # Get current action data and settings
        model = await self.get_model(chat_iid)
        actions = await self.get_actions(model)
        current_action_data = None
        for act in actions:
            if act.name == action_name:
                current_action_data = act.data
                break
        settings = action.settings(_convert_action_data_to_model(action, current_action_data or {}))

        if setting_id not in settings:
            await message.reply(_("Invalid setting."))
            await state.clear()
            return

        setting = settings[setting_id]
        if not setting.setup_confirm:
            await message.reply(_("Setting configuration not available."))
            await state.clear()
            return

        try:
            # Call the setting's setup_confirm function
            setting_data = await setting.setup_confirm(message, self.data)

            # Convert Pydantic model to dictionary if needed
            if setting_data and hasattr(setting_data, "model_dump"):
                setting_data_dict = setting_data.model_dump(mode="json")
            else:
                setting_data_dict = setting_data

            # Update action data with new setting - use the returned data
            # For most settings, the setting_data should be the new action data
            updated_action_data = setting_data_dict if setting_data_dict else (current_action_data or {})

            # Stage the updated action data (no DB write yet)
            await set_action_data(state, updated_action_data)

            # Show configured action with settings buttons
            callback_prefix = state_data.get("setting_setup_callback_prefix", self.callback_prefix)

            await _show_action_configured_message(
                message, action_name, chat_iid, callback_prefix, self.success_message, updated_action_data
            )
            # Exit interactive setup state but keep staged data
            await state.set_state(None)

        except ActionSetupTryAgainException:
            # Let user try again - don't clear state
            pass
