from __future__ import annotations

from typing import Optional

from aiogram.types import CallbackQuery, Message
from beanie import PydanticObjectId
from pydantic import ValidationError


def _convert_action_data_to_model(action, action_data):
    """Convert dictionary action data to Pydantic model using action's data_object."""
    if action_data is None:
        return action.default_data

    # If it's already a Pydantic model, return as-is
    if hasattr(action_data, "model_dump"):
        return action_data

    # If it's a dictionary, convert it to the proper Pydantic model
    if isinstance(action_data, dict) and action_data:
        try:
            return action.data_object(**action_data)
        except (ValidationError, TypeError, ValueError):
            # If validation fails (e.g., wrong fields), fall back to default data
            # This can happen when action data was stored for a different action type
            return action.default_data

    # Fallback to default data
    return action.default_data


async def _show_action_configured_message(
    event: CallbackQuery | Message,
    action_name: str,
    chat_tid: PydanticObjectId,
    callback_prefix: str,
    success_message: str,
    action_data: Optional[dict] = None,
    *,
    show_delete: bool = True,
    show_cancel: bool = True,
) -> None:
    """Deprecated: rendering moved to WizardRenderer. Delegates for backward compatibility."""

    from sophie_bot.modules.utils_.action_config_wizard.renderer import WizardRenderer
    # Local import to avoid circular import during module initialization

    await WizardRenderer.show_action_configured_message(
        event,
        action_name=action_name,
        chat_tid=chat_tid,
        callback_prefix=callback_prefix,
        success_message=success_message,
        action_data=action_data,
        show_delete=show_delete,
        show_cancel=show_cancel,
    )
