"""
Action Configuration Wizard System

A comprehensive system for creating interactive action configuration interfaces
for modules. Provides standardized wizards with button-based action selection,
interactive setup workflows, and settings management.

Example usage:

    from sophie_bot.modules.utils_.action_config_wizard import create_action_config_system

    # Create handler classes for your module
    (
        MyActionHandler,
        MyActionCallbackHandler,
        MyActionSetupHandler,
        MyActionDoneHandler,
        MyActionCancelHandler,
        MyActionSettingsHandler,
    ) = create_action_config_system(
        module_name="my_module",
        callback_prefix="my_module_action",
        wizard_title="My Module Action Configuration",
        success_message="Action updated successfully!",
        get_model_func=get_my_model,
        get_current_action_func=get_current_action,
        get_current_action_data_func=get_current_action_data,
        update_action_func=update_my_action,
        command_filter=CMDFilter("myaction"),
        admin_filter=UserRestricting(admin=True),
    )

The system automatically handles:
- Action selection with button interface
- Interactive setup workflows for complex actions
- Settings configuration for actions with additional parameters
- FSM state management for multi-step processes
- Proper data conversion between Pydantic models and dictionaries
- Error handling and user feedback
"""

from .factory import create_action_config_system

# Export the main factory function
__all__ = ["create_action_config_system"]
