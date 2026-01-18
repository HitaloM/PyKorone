from __future__ import annotations

import time
from datetime import date, datetime
from datetime import time as dt_time
from datetime import timedelta
from enum import Enum
from typing import Any, Optional, Tuple

from aiogram.fsm.context import FSMContext
from beanie import PydanticObjectId
from bson.errors import InvalidId


def _sanitize_for_json(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dt_time):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        try:
            return obj.total_seconds()
        except (OverflowError, ValueError):
            return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(mode="json")
        except (AttributeError, TypeError, ValueError):
            try:
                return obj.dict()
            except (AttributeError, TypeError):
                return str(obj)
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in obj]
    return str(obj)


ACW_SESSION_TTL_SECONDS = 20 * 60  # 20 minutes

# Keys used in FSM data for the Action Config Wizard session
K_MODULE = "acw_module"
K_CHAT_IID = "acw_chat_iid"
K_STARTED_AT = "acw_started_at"
K_ACTION_NAME = "acw_action_name"
K_ACTION_DATA = "acw_action_data"


async def _now() -> float:
    return time.time()


async def _expired(started_at: Optional[float]) -> bool:
    if started_at is None:
        return True
    return (await _now()) - started_at > ACW_SESSION_TTL_SECONDS


async def clear_session(state: FSMContext) -> None:
    """Clear all ACW session-related keys from FSM data."""
    data = await state.get_data()
    for key in (K_MODULE, K_CHAT_IID, K_STARTED_AT, K_ACTION_NAME, K_ACTION_DATA):
        if key in data:
            del data[key]
    await state.update_data(**data)


async def ensure_session(state: FSMContext, module_name: str, chat_iid: PydanticObjectId) -> None:
    """Ensure a valid ACW session exists; start a new one or refresh if needed.

    - Ties the session to (module_name, chat_iid)
    - Enforces TTL: if expired or different module/chat, resets the session
    """
    data = await state.get_data()
    started_at = data.get(K_STARTED_AT)
    # Store internal IDs as strings in FSM to keep JSON-serializable
    stored_chat_iid = data.get(K_CHAT_IID)
    same_context = data.get(K_MODULE) == module_name and stored_chat_iid == str(chat_iid)

    if (not same_context) or (await _expired(started_at)):
        # Reset and start new session
        data[K_MODULE] = module_name
        data[K_CHAT_IID] = str(chat_iid)
        data[K_STARTED_AT] = await _now()
        data.pop(K_ACTION_NAME, None)
        data.pop(K_ACTION_DATA, None)
        await state.update_data(**data)
    else:
        # Refresh TTL (optional; keep original start to allow absolute TTL)
        pass


async def set_action(state: FSMContext, action_name: str) -> None:
    data = await state.get_data()
    data[K_ACTION_NAME] = action_name
    await state.update_data(**data)


async def set_action_data(state: FSMContext, action_data: dict | None) -> None:
    data = await state.get_data()
    data[K_ACTION_DATA] = _sanitize_for_json(action_data or {})
    await state.update_data(**data)


async def get_staged(state: FSMContext) -> Tuple[Optional[PydanticObjectId], Optional[str], Optional[dict[str, Any]]]:
    data = await state.get_data()
    chat_iid_raw = data.get(K_CHAT_IID)
    chat_iid: Optional[PydanticObjectId]
    try:
        chat_iid = PydanticObjectId(chat_iid_raw) if chat_iid_raw else None
    except (InvalidId, TypeError):
        chat_iid = None
    action_name = data.get(K_ACTION_NAME)
    action_data = data.get(K_ACTION_DATA)
    return chat_iid, action_name, action_data


async def is_active(state: FSMContext, module_name: str, chat_iid: PydanticObjectId) -> bool:
    data = await state.get_data()
    if data.get(K_MODULE) != module_name or data.get(K_CHAT_IID) != str(chat_iid):
        return False
    return not (await _expired(data.get(K_STARTED_AT)))
