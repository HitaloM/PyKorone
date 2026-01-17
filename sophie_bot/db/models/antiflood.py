from __future__ import annotations

from typing import Optional, Literal

from beanie import Document, PydanticObjectId
from pydantic import Field, model_validator

from ._link_type import Link
from .chat import ChatModel
from .filters import FilterActionType

LEGACY_ACTION_TYPE = Literal["mute"] | Literal["kick"] | Literal["ban"]
LEGACY_ACTIONS = {"mute", "kick", "ban"}
LEGACY_ACTIONS_TO_MODERN = {"mute": "mute_user", "kick": "kick_user", "ban": "ban_user"}


class AntifloodModel(Document):
    chat: Link[ChatModel]
    enabled: Optional[bool] = True
    message_count: int = Field(default=5, ge=1, le=100)  # Number of messages in 30s window
    actions: list[FilterActionType] = []
    action: Optional[LEGACY_ACTION_TYPE] = None  # Legacy action

    class Settings:
        name = "antiflood"

    @model_validator(mode="after")
    def handle_legacy_actions(self) -> "AntifloodModel":
        """Convert legacy action names to FilterActionType objects."""
        if not self.actions and self.action in LEGACY_ACTIONS:
            legacy_action = self.action
            modern_name = LEGACY_ACTIONS_TO_MODERN[str(legacy_action)]
            self.actions = [FilterActionType(name=modern_name, data={})]
        return self

    @staticmethod
    async def get_by_chat_iid(chat_iid: PydanticObjectId) -> AntifloodModel:
        """Get or create antiflood settings for a chat using database internal ID."""
        existing = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)
        if existing:
            return existing

        return AntifloodModel(chat=chat_iid)

    @staticmethod
    async def set_antiflood_count(chat_iid: PydanticObjectId, message_count: int) -> AntifloodModel:
        """Set the message count threshold for antiflood using internal DB ID (chat_iid)."""
        model = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid) or AntifloodModel(chat=chat_iid)

        model.message_count = message_count
        await model.save()
        return model

    @staticmethod
    async def add_antiflood_action(
        chat_iid: PydanticObjectId, action_name: str, action_data: Optional[dict] = None
    ) -> AntifloodModel:
        """Add an action for antiflood violations using internal DB ID (chat_iid)."""
        action = FilterActionType(name=action_name, data=action_data or {})

        model = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)
        if model is None:
            chat = await ChatModel.get_by_iid(chat_iid)
            if chat is None:
                raise ValueError(f"Chat with internal ID {chat_iid!s} not found")
            model = AntifloodModel(chat=chat)

        actions = list(model.actions or [])
        actions.append(action)
        model.actions = actions

        await model.save()
        return model

    @staticmethod
    async def remove_antiflood_action(chat_iid: PydanticObjectId, action_name: str) -> AntifloodModel:
        """Remove an action for antiflood violations using internal DB ID (chat_iid)."""
        model = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)
        if model is None:
            chat = await ChatModel.get_by_iid(chat_iid)
            if chat is None:
                raise ValueError(f"Chat with internal ID {chat_iid!s} not found")
            model = AntifloodModel(chat=chat)
            # No actions to remove on a fresh model
            await model.save()
            return model

        model.actions = [action for action in model.actions if action.name != action_name]
        await model.save()
        return model
