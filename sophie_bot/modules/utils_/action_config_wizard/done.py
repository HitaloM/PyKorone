from __future__ import annotations

from typing import Any, TypeVar

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from beanie import PydanticObjectId

from sophie_bot.utils.i18n import gettext as _
from .base import ActionConfigDoneHandlerABC
from .callbacks import ACWCoreCallback
from .renderer import WizardRenderer
from .service import clear_session, get_staged

# Type variable for the model type that stores action configuration
ModelType = TypeVar("ModelType")


class ActionConfigDoneHandlerMixin(ActionConfigDoneHandlerABC):
    """Mixin providing concrete implementation for the done handler."""

    @staticmethod
    def create_filters(callback_prefix: str) -> tuple[CallbackType, ...]:
        """Create filters for this callback handler."""
        return (ACWCoreCallback.filter((F.mod == callback_prefix) & (F.op == "done")),)

    async def handle(self) -> Any:
        """Handle setup completion."""
        callback_query: CallbackQuery = self.event
        state = self.data.get("state")

        # On Done, persist staged data before clearing the session
        if isinstance(state, FSMContext):
            chat_tid, action_name, action_data = await get_staged(state)
            if chat_tid is not None and action_name:
                # Ensure dict for storage
                if (
                    action_data is not None
                    and hasattr(action_data, "model_dump")
                    and callable(getattr(action_data, "model_dump", None))
                ):
                    action_data = action_data.model_dump(mode="json")  # type: ignore[union-attr]
                await self.add_action(chat_tid, action_name, action_data or {})

        if isinstance(state, FSMContext):
            # Clear staged session data
            await clear_session(state)
            await state.clear()

        # Instead of just showing "Done", redirect back to home page
        if callback_query.message and isinstance(callback_query.message, Message):
            await self._show_home_page(callback_query)

        await callback_query.answer(_("Saved"))

    async def _show_home_page(self, callback_query: CallbackQuery) -> None:
        """Show the action configuration home page after completion (via renderer)."""
        msg = callback_query.message
        if not msg or not isinstance(msg, Message):
            return
        chat_tid: PydanticObjectId = self.connection.db_model.iid
        state = self.data.get("state")

        html, markup = await WizardRenderer.render_home_page(
            self,
            chat_iid=chat_tid,
            chat_title=msg.chat.title,
            state=state,
        )
        await msg.edit_text(html, reply_markup=markup)
