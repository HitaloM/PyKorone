from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar
from beanie import PydanticObjectId

from aiogram.handlers import CallbackQueryHandler

from sophie_bot.db.models.filters import FilterActionType
from sophie_bot.utils.handlers import SophieMessageHandler, SophieCallbackQueryHandler

# Type variable for the model type that stores action configuration
ModelType = TypeVar("ModelType")


class ActionConfigDataAccessABC(Generic[ModelType], ABC):
    """Shared abstract data-access contract for action config components."""

    @abstractmethod
    async def get_model(self, chat_iid: PydanticObjectId) -> ModelType:
        """Get the model instance for the chat (database internal ID - chat_iid)."""
        pass

    @abstractmethod
    async def get_actions(self, model: ModelType) -> list[FilterActionType]:
        """Get the list of actions from the model."""
        pass

    @abstractmethod
    async def add_action(
        self, chat_iid: PydanticObjectId, action_name: str, action_data: Optional[dict] = None
    ) -> None:
        """Add an action to the model using database internal ID (chat_iid)."""
        pass

    @abstractmethod
    async def remove_action(self, chat_iid: PydanticObjectId, action_id: str) -> None:
        """Remove an action from the model using database internal ID (chat_iid)."""
        pass


class ActionConfigWizardABC(SophieMessageHandler, ActionConfigDataAccessABC[ModelType], Generic[ModelType], ABC):
    """
    Abstract base class for creating action configuration wizards.

    This class provides a standardized interface for modules to implement
    action configuration with buttons and callback handling. It can be used
    by antiflood, filters, and other modules that need action configuration.
    """

    # Override these in subclasses
    module_name: str = ""  # e.g., "antiflood", "filters"
    callback_prefix: str = ""  # e.g., "antiflood_action", "filter_action"
    wizard_title: str = ""  # e.g., "Antiflood Action Configuration"


class ActionConfigCallbackABC(
    SophieCallbackQueryHandler, ActionConfigDataAccessABC[ModelType], Generic[ModelType], ABC
):
    """
    Abstract base class for handling action configuration callbacks.

    This handles the button clicks from the action configuration wizard.
    """

    # Override these in subclasses
    callback_prefix: str = ""  # e.g., "antiflood_action", "filter_action"
    success_message: str = ""  # e.g., "Antiflood action updated successfully!"


class ActionConfigSetupHandlerABC(SophieMessageHandler, ActionConfigDataAccessABC[ModelType], Generic[ModelType], ABC):
    """
    Abstract base class for handling interactive setup messages.

    This processes user input during the interactive setup workflow.
    """

    # Override these in subclasses
    callback_prefix: str = ""  # e.g., "antiflood_action", "filter_action"
    success_message: str = ""


class ActionConfigSettingsHandlerABC(
    SophieCallbackQueryHandler, ActionConfigDataAccessABC[ModelType], Generic[ModelType], ABC
):
    """
    Abstract base class for handling settings button clicks.

    This handles clicks on settings buttons shown after action configuration.
    """

    # Override these in subclasses
    callback_prefix: str = ""
    success_message: str = ""

    @abstractmethod
    async def get_model(self, chat_iid: PydanticObjectId) -> ModelType:
        """Get the model instance for the chat (database internal ID - chat_iid)."""
        pass

    @abstractmethod
    async def get_actions(self, model: ModelType) -> list[FilterActionType]:
        """Get the list of actions from the model."""
        pass

    @abstractmethod
    async def add_action(
        self, chat_iid: PydanticObjectId, action_name: str, action_data: Optional[dict] = None
    ) -> None:
        """Add an action to the model using database internal ID (chat_iid)."""
        pass

    @abstractmethod
    async def remove_action(self, chat_iid: PydanticObjectId, action_id: str) -> None:
        """Remove an action from the model using database internal ID (chat_iid)."""
        pass


class ActionConfigDoneHandlerABC(
    SophieCallbackQueryHandler, ActionConfigDataAccessABC[ModelType], Generic[ModelType], ABC
):
    """
    Abstract base class for handling setup completion (done).
    """

    # Override these in subclasses
    callback_prefix: str = ""
    success_message: str = ""

    @abstractmethod
    async def get_model(self, chat_iid: PydanticObjectId) -> ModelType:
        """Get the model instance for the chat (database internal ID - chat_iid)."""
        pass

    @abstractmethod
    async def get_actions(self, model: ModelType) -> list[FilterActionType]:
        """Get the list of actions from the model."""
        pass

    @abstractmethod
    async def add_action(
        self, chat_iid: PydanticObjectId, action_name: str, action_data: Optional[dict] = None
    ) -> None:
        """Add an action to the model using database internal ID (chat_iid)."""
        pass

    @abstractmethod
    async def remove_action(self, chat_iid: PydanticObjectId, action_id: str) -> None:
        """Remove an action from the model using database internal ID (chat_iid)."""
        pass


class ActionConfigCancelHandlerABC(CallbackQueryHandler, ActionConfigDataAccessABC[ModelType], Generic[ModelType], ABC):
    """
    Abstract base class for handling setup cancellation.
    """

    # Override these in subclasses
    callback_prefix: str = ""
    success_message: str = ""

    @abstractmethod
    async def get_model(self, chat_iid: PydanticObjectId) -> ModelType:
        """Get the model instance for the chat (database internal ID - chat_iid)."""
        pass

    @abstractmethod
    async def get_actions(self, model: ModelType) -> list[FilterActionType]:
        """Get the list of actions from the model."""
        pass

    @abstractmethod
    async def add_action(
        self, chat_iid: PydanticObjectId, action_name: str, action_data: Optional[dict] = None
    ) -> None:
        """Add an action to the model using database internal ID (chat_iid)."""
        pass

    @abstractmethod
    async def remove_action(self, chat_iid: PydanticObjectId, action_id: str) -> None:
        """Remove an action from the model using database internal ID (chat_iid)."""
        pass
