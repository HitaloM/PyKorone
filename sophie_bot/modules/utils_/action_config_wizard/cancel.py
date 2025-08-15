from __future__ import annotations

from typing import Any, TypeVar

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from sophie_bot.utils.i18n import gettext as _

from .base import ActionConfigCancelHandlerABC
from .callbacks import ACWCoreCallback
from .service import clear_session

# Type variable for the model type that stores action configuration
ModelType = TypeVar("ModelType")


class ActionConfigCancelHandlerMixin(ActionConfigCancelHandlerABC):
    """Mixin providing concrete implementation for the cancel handler."""

    @staticmethod
    def create_filters(callback_prefix: str) -> tuple[CallbackType, ...]:
        """Create filters for this callback handler."""
        return (ACWCoreCallback.filter((F.mod == callback_prefix) & (F.op == "cancel")),)

    async def handle(self) -> Any:
        """Handle setup cancellation."""
        callback_query: CallbackQuery = self.event
        state = self.data.get("state")

        if isinstance(state, FSMContext):
            # Clear staged session data
            await clear_session(state)
            await state.clear()

        if callback_query.message and isinstance(callback_query.message, Message):
            await callback_query.message.edit_text(_("Action configuration cancelled."))

        await callback_query.answer(_("Cancelled"))
