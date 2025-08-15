from __future__ import annotations

from typing import Any, Optional

from aiogram.fsm.context import FSMContext
from beanie import PydanticObjectId

from .service import ensure_session, get_staged, is_active, set_action, set_action_data


class WizardController:
    """Controller to orchestrate Action Config Wizard state and decisions."""

    @staticmethod
    async def stage_action(
        state: FSMContext,
        module_name: str,
        chat_iid: PydanticObjectId,
        action_name: str,
        action_data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Ensure session and stage the selected action without persisting it."""
        await ensure_session(state, module_name, chat_iid)
        await set_action(state, action_name)
        await set_action_data(state, action_data or {})

    @staticmethod
    async def has_staged_changes(state: FSMContext | None, module_name: str, chat_iid: PydanticObjectId) -> bool:
        """Return True if there is staged action data for this module and chat."""
        if state is None or not isinstance(state, FSMContext):
            return False
        if not await is_active(state, module_name, chat_iid):
            return False
        staged_chat_iid, action_name, _ = await get_staged(state)
        return bool(action_name) and (staged_chat_iid == chat_iid)
