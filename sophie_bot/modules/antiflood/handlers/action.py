from __future__ import annotations

from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.db.models.filters import FilterActionType


get_antiflood_model = AntifloodModel.get_by_chat_iid


async def get_actions(model: AntifloodModel) -> list[FilterActionType]:
    """Get the list of actions from the model."""
    return model.actions


add_action = AntifloodModel.add_antiflood_action
remove_action = AntifloodModel.remove_antiflood_action
