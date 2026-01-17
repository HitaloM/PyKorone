from __future__ import annotations

from typing import Any, Optional

from aiogram import F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from beanie import PydanticObjectId
from pymongo.errors import PyMongoError

from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.utils.i18n import gettext as _
from .base import ActionConfigCallbackABC
from .callbacks import ACWCoreCallback
from .fsm import ActionConfigFSM
from .renderer import WizardRenderer
from .service import ensure_session


class ActionConfigCallbackMixin(ActionConfigCallbackABC):
    """Mixin providing concrete implementation for the callback handler."""

    @staticmethod
    def create_filters(callback_prefix: str) -> tuple[CallbackType, ...]:
        """Create filters for this callback handler."""
        return (ACWCoreCallback.filter((F.mod == callback_prefix)),)

    async def handle(self) -> Any:
        """Handle callback query for action selection."""
        callback_query: CallbackQuery = self.event
        data: ACWCoreCallback = self.data["callback_data"]

        op = data.op
        if op == "add":
            await self._handle_add_action(callback_query)
        elif op == "remove" and data.name:
            await self._handle_remove_action(callback_query, data.name)
        elif op == "configure" and data.name:
            await self._handle_configure_action(callback_query, data.name)
        elif op == "back":
            await self._handle_back_action(callback_query)
        elif op in ("done", "cancel"):
            # Delegate to dedicated Done/Cancel handlers
            raise SkipHandler
        elif op == "select" and data.name:
            await self._handle_select_action(callback_query, data.name)
        else:
            await callback_query.answer(_("Invalid callback data"))

    async def _handle_add_action(self, callback_query: CallbackQuery):
        """Show a list of actions to add (via renderer)."""
        # Enforce single-action policy if configured
        allow_multiple = getattr(self, "allow_multiple_actions", True)
        if not allow_multiple and callback_query.message and isinstance(callback_query.message, Message):
            chat_tid: PydanticObjectId = self.connection.db_model.iid
            model = await self.get_model(chat_tid)
            actions = await self.get_actions(model)

            if actions:
                await callback_query.answer(_("Only one action is allowed for this filter"))
                await self._show_home_page(callback_query)
                return
        if not callback_query.message or not isinstance(callback_query.message, Message):
            await callback_query.answer(_("Message not found."))
            return
        from .renderer import WizardRenderer

        text, markup = await WizardRenderer.render_add_action_list(self, chat_tid=callback_query.message.chat.id)
        await callback_query.message.edit_text(text, reply_markup=markup)

    async def _handle_remove_action(self, callback_query: CallbackQuery, action_id: str):
        """Remove an action and return to home page."""
        if not callback_query.message or not isinstance(callback_query.message, Message):
            await callback_query.answer(_("Message not found."))
            return
        chat_tid: PydanticObjectId = self.connection.db_model.iid
        await self.remove_action(chat_tid, action_id)
        await callback_query.answer(_("Action removed."))
        # Refresh the wizard message to the home page
        await self._show_home_page(callback_query)

    async def _handle_select_action(self, callback_query: CallbackQuery, action_name: str):
        """Handle the selection of an action to add (immutably stage first)."""
        if action_name not in ALL_MODERN_ACTIONS:
            await callback_query.answer(_("Invalid action"))
            return

        if not callback_query.message or not isinstance(callback_query.message, Message):
            await callback_query.answer(_("Message not found."))
            return
        chat_tid: PydanticObjectId = self.connection.db_model.iid

        # Enforce single-action policy if configured and one already exists
        allow_multiple = getattr(self, "allow_multiple_actions", True)
        if not allow_multiple:
            await callback_query.answer(_("Only one action is allowed for this filter"))
            await self._show_home_page(callback_query)
            return

        action = ALL_MODERN_ACTIONS[action_name]

        if action.interactive_setup and action.interactive_setup.setup_message:
            await self._start_interactive_setup(callback_query, action_name, chat_tid)
            return

        # Non-interactive: stage, do not persist
        default_data = action.default_data
        if default_data is not None and hasattr(default_data, "model_dump"):
            default_data = default_data.model_dump(mode="json")

        state = self.data.get("state")
        if isinstance(state, FSMContext):
            from .controller import WizardController

            await WizardController.stage_action(
                state, getattr(self, "module_name", ""), chat_tid, action_name, default_data
            )

        # Show configured screen without Delete/Cancel for new unsaved action
        from .renderer import WizardRenderer

        await WizardRenderer.show_action_configured_message(
            callback_query,
            action_name=action_name,
            chat_tid=chat_tid,
            callback_prefix=self.callback_prefix,
            success_message=self.success_message,
            action_data=default_data,
            show_delete=False,
            show_cancel=False,
        )

    async def _start_interactive_setup(
        self, callback_query: CallbackQuery, action_name: str, chat_tid: PydanticObjectId
    ) -> None:
        """Start interactive setup process for an action."""
        action = ALL_MODERN_ACTIONS[action_name]

        state = self.data.get("state")
        if not isinstance(state, FSMContext):
            await callback_query.answer(_("State management not available"))
            return

        await ensure_session(state, getattr(self, "module_name", ""), chat_tid)
        await state.update_data(
            action_setup_name=action_name,
            action_setup_chat_tid=str(chat_tid),
            action_setup_callback_prefix=self.callback_prefix,
        )
        await state.set_state(ActionConfigFSM.interactive_setup)

        if not action.interactive_setup or not action.interactive_setup.setup_message:
            await callback_query.answer(_("Action setup not properly configured"))
            return

        setup_message = await action.interactive_setup.setup_message(callback_query, self.data)

        reply_markup = setup_message.reply_markup
        if not reply_markup:
            from aiogram.types import InlineKeyboardMarkup

            reply_markup = InlineKeyboardMarkup(inline_keyboard=[])

        reply_markup.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=_("🔙 Back"), callback_data=ACWCoreCallback(mod=self.callback_prefix, op="back").pack()
                )
            ]
        )

        if callback_query.message and isinstance(callback_query.message, Message):
            await callback_query.message.edit_text(setup_message.text, reply_markup=reply_markup)

    async def _show_action_configured(
        self,
        event: CallbackQuery | Message,
        action_name: str,
        chat_tid: PydanticObjectId,
        action_data: Optional[dict] = None,
    ) -> None:
        """Show action configured message with settings buttons if available."""
        if action_data is None:
            try:
                model = await self.get_model(chat_tid)
                actions = await self.get_actions(model)
                # Find the action we just configured
                for action in actions:
                    if action.name == action_name:
                        action_data = action.data
                        break
            except PyMongoError:
                action_data = ALL_MODERN_ACTIONS[action_name].default_data

        from .renderer import WizardRenderer

        await WizardRenderer.show_action_configured_message(
            event,
            action_name=action_name,
            chat_tid=chat_tid,
            callback_prefix=self.callback_prefix,
            success_message=self.success_message,
            action_data=action_data,
        )

    async def _handle_configure_action(self, callback_query: CallbackQuery, action_name: str):
        """Handle configuration of an existing action."""
        if not callback_query.message or not isinstance(callback_query.message, Message):
            await callback_query.answer(_("Message not found."))
            return

        chat_tid: PydanticObjectId = self.connection.db_model.iid

        # Get the current action data
        try:
            model = await self.get_model(chat_tid)
            actions = await self.get_actions(model)
            action_data = None
            for action in actions:
                if action.name == action_name:
                    action_data = action.data
                    break
        except PyMongoError:
            action_data = None

        if action_name not in ALL_MODERN_ACTIONS:
            await callback_query.answer(_("Invalid action"))
            return

        # Show the action configuration screen with settings and delete option
        await self._show_action_configured(callback_query, action_name, chat_tid, action_data)

    async def _handle_back_action(self, callback_query: CallbackQuery):
        """Handle back button - return to home page."""
        if not callback_query.message or not isinstance(callback_query.message, Message):
            await callback_query.answer(_("Message not found."))
            return

        await self._show_home_page(callback_query)
        await callback_query.answer()

    async def _show_home_page(self, callback_query: CallbackQuery) -> None:
        """Show the action configuration home page (via renderer)."""
        msg = callback_query.message
        if not msg or not isinstance(msg, Message):
            return
        state = self.data.get("state")

        chat_iid: PydanticObjectId = self.connection.db_model.iid

        html, markup = await WizardRenderer.render_home_page(
            self,
            chat_iid=chat_iid,
            chat_title=msg.chat.title,
            state=state,
        )
        await msg.edit_text(html, reply_markup=markup)
