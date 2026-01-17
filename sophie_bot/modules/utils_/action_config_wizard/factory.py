from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Optional, TypeVar

from aiogram import Router
from beanie import PydanticObjectId

from ....db.models.filters import FilterActionType
from .base import (
    ActionConfigCallbackABC,
    ActionConfigCancelHandlerABC,
    ActionConfigDoneHandlerABC,
    ActionConfigSettingsHandlerABC,
    ActionConfigSetupHandlerABC,
    ActionConfigWizardABC,
)
from .callback import ActionConfigCallbackMixin
from .cancel import ActionConfigCancelHandlerMixin
from .done import ActionConfigDoneHandlerMixin
from .settings import ActionConfigSettingsHandlerMixin
from .setup import ActionConfigSetupHandlerMixin
from .wizard import ActionConfigWizardMixin

ModelT = TypeVar("ModelT")

GetModelFunc = Callable[[PydanticObjectId], Awaitable[ModelT]]
GetActionsFunc = Callable[[ModelT], Awaitable[list[FilterActionType]]]
AddActionFunc = Callable[[PydanticObjectId, str, Optional[dict]], Awaitable[None]]
RemoveActionFunc = Callable[[PydanticObjectId, str], Awaitable[None]]


def _invoke(func: Any, self: Any, *args: Any):
    try:
        sig = inspect.signature(func)
        if len(sig.parameters) >= len(args) + 1:
            return func(self, *args)
    except (ValueError, TypeError):
        pass
    return func(*args)


def create_action_config_system(
    module_name: str,
    callback_prefix: str,
    wizard_title: str,
    success_message: str,
    get_model_func: GetModelFunc | Any,
    get_actions_func: GetActionsFunc | Any,
    add_action_func: AddActionFunc | Any,
    remove_action_func: RemoveActionFunc | Any,
    command_filter: Any,
    admin_filter: Any,
    *,
    allow_multiple_actions: bool = True,
):
    """
    Factory function to create a complete action configuration system for a module.

    Returns a tuple of (WizardHandler, CallbackHandler, SetupHandler, DoneHandler, CancelHandler, SettingsHandler)
    that can be registered in the module.
    """

    # Create wizard handler class
    wizard_attrs = {
        "module_name": module_name,
        "callback_prefix": callback_prefix,
        "wizard_title": wizard_title,
        "allow_multiple_actions": allow_multiple_actions,
        "filters": lambda: (command_filter, admin_filter),
        "get_model": lambda self, chat_iid: _invoke(get_model_func, self, chat_iid),
        "get_actions": lambda self, model: _invoke(get_actions_func, self, model),
        "add_action": lambda self, chat_iid, action_name, action_data=None: _invoke(
            add_action_func, self, chat_iid, action_name, action_data
        ),
        "remove_action": lambda self, chat_iid, action_id: _invoke(remove_action_func, self, chat_iid, action_id),
    }
    ModuleActionWizard = type("ModuleActionWizard", (ActionConfigWizardMixin, ActionConfigWizardABC), wizard_attrs)

    # Create callback handler class
    callback_attrs = {
        "module_name": module_name,
        "callback_prefix": callback_prefix,
        "success_message": success_message,
        "allow_multiple_actions": allow_multiple_actions,
        "filters": lambda: ActionConfigCallbackMixin.create_filters(callback_prefix),
        "get_model": lambda self, chat_iid: _invoke(get_model_func, self, chat_iid),
        "get_actions": lambda self, model: _invoke(get_actions_func, self, model),
        "add_action": lambda self, chat_iid, action_name, action_data=None: _invoke(
            add_action_func, self, chat_iid, action_name, action_data
        ),
        "remove_action": lambda self, chat_iid, action_id: _invoke(remove_action_func, self, chat_iid, action_id),
    }
    ModuleActionCallback = type(
        "ModuleActionCallback", (ActionConfigCallbackMixin, ActionConfigCallbackABC), callback_attrs
    )

    # Create setup handler class for interactive configuration
    setup_attrs = {
        "module_name": module_name,
        "callback_prefix": callback_prefix,
        "success_message": success_message,
        "allow_multiple_actions": allow_multiple_actions,
        "filters": lambda: ActionConfigSetupHandlerMixin.create_filters(),
        "get_model": lambda self, chat_iid: _invoke(get_model_func, self, chat_iid),
        "get_actions": lambda self, model: _invoke(get_actions_func, self, model),
        "add_action": lambda self, chat_iid, action_name, action_data=None: _invoke(
            add_action_func, self, chat_iid, action_name, action_data
        ),
        "remove_action": lambda self, chat_iid, action_id: _invoke(remove_action_func, self, chat_iid, action_id),
    }
    ModuleActionSetup = type(
        "ModuleActionSetup", (ActionConfigSetupHandlerMixin, ActionConfigSetupHandlerABC), setup_attrs
    )

    # Create done handler class
    done_attrs = {
        "module_name": module_name,
        "callback_prefix": callback_prefix,
        "success_message": success_message,
        "allow_multiple_actions": allow_multiple_actions,
        "filters": lambda: ActionConfigDoneHandlerMixin.create_filters(callback_prefix),
        "get_model": lambda self, chat_iid: _invoke(get_model_func, self, chat_iid),
        "get_actions": lambda self, model: _invoke(get_actions_func, self, model),
        "add_action": lambda self, chat_iid, action_name, action_data=None: _invoke(
            add_action_func, self, chat_iid, action_name, action_data
        ),
        "remove_action": lambda self, chat_iid, action_id: _invoke(remove_action_func, self, chat_iid, action_id),
    }
    ModuleActionDone = type("ModuleActionDone", (ActionConfigDoneHandlerMixin, ActionConfigDoneHandlerABC), done_attrs)

    # Create cancel handler class
    cancel_attrs = {
        "module_name": module_name,
        "callback_prefix": callback_prefix,
        "success_message": success_message,
        "filters": lambda: ActionConfigCancelHandlerMixin.create_filters(callback_prefix),
        "get_model": lambda self, chat_iid: _invoke(get_model_func, self, chat_iid),
        "get_actions": lambda self, model: _invoke(get_actions_func, self, model),
        "add_action": lambda self, chat_iid, action_name, action_data=None: _invoke(
            add_action_func, self, chat_iid, action_name, action_data
        ),
        "remove_action": lambda self, chat_iid, action_id: _invoke(remove_action_func, self, chat_iid, action_id),
    }
    ModuleActionCancel = type(
        "ModuleActionCancel", (ActionConfigCancelHandlerMixin, ActionConfigCancelHandlerABC), cancel_attrs
    )

    # Create settings handler class
    settings_attrs = {
        "module_name": module_name,
        "callback_prefix": callback_prefix,
        "success_message": success_message,
        "filters": lambda: ActionConfigSettingsHandlerMixin.create_filters(callback_prefix),
        "get_model": lambda self, chat_iid: _invoke(get_model_func, self, chat_iid),
        "get_actions": lambda self, model: _invoke(get_actions_func, self, model),
        "add_action": lambda self, chat_iid, action_name, action_data=None: _invoke(
            add_action_func, self, chat_iid, action_name, action_data
        ),
        "remove_action": lambda self, chat_iid, action_id: _invoke(remove_action_func, self, chat_iid, action_id),
    }
    ModuleActionSettings = type(
        "ModuleActionSettings", (ActionConfigSettingsHandlerMixin, ActionConfigSettingsHandlerABC), settings_attrs
    )

    return (
        ModuleActionWizard,
        ModuleActionCallback,
        ModuleActionSetup,
        ModuleActionDone,
        ModuleActionCancel,
        ModuleActionSettings,
    )


def register_action_config_system(router: Router, *args, **kwargs):
    """Convenience helper to create and register all ACW handlers on a router.

    Returns the tuple of generated handler classes in the same order as
    create_action_config_system.
    """
    (
        WizardHandler,
        CallbackHandler,
        SetupHandler,
        DoneHandler,
        CancelHandler,
        SettingsHandler,
    ) = create_action_config_system(*args, **kwargs)

    # Register the main wizard (message handler). Prefer class-provided register.
    if hasattr(WizardHandler, "register"):
        # SophieMessageHandler provides register with proper flags
        WizardHandler.register(router)
    else:  # pragma: no cover - defensive fallback
        router.message.register(WizardHandler, *WizardHandler.filters())

    # Message handler for interactive setup
    router.message.register(SetupHandler, *SetupHandler.filters())

    # Callback query handlers
    router.callback_query.register(CallbackHandler, *CallbackHandler.filters())
    router.callback_query.register(DoneHandler, *DoneHandler.filters())
    router.callback_query.register(CancelHandler, *CancelHandler.filters())
    router.callback_query.register(SettingsHandler, *SettingsHandler.filters())

    return (
        WizardHandler,
        CallbackHandler,
        SetupHandler,
        DoneHandler,
        CancelHandler,
        SettingsHandler,
    )
