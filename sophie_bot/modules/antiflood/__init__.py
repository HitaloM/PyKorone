from aiogram import Router

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.antiflood.config import FLOOD_WINDOW_SECONDS
from sophie_bot.modules.antiflood.handlers.action import (
    add_action,
    get_actions,
    get_antiflood_model,
    remove_action,
)
from sophie_bot.modules.antiflood.handlers.setflood import SetFloodHandler
from sophie_bot.modules.antiflood.handlers.status import AntifloodStatusHandler
from sophie_bot.modules.antiflood.middlewares.antiflood import AntifloodMiddleware
from sophie_bot.modules.utils_.action_config_wizard.factory import (
    register_action_config_system,
)
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Antiflood")
__module_emoji__ = "🚫"
__module_info__ = l_(
    f"Antiflood protection automatically detects and punishes users who send too many messages in a short time period. "
    f"Configure the message threshold (default: 5 messages in {FLOOD_WINDOW_SECONDS} seconds) and action to take (ban, kick, mute, temporary mute, or temporary ban)."
)

router = Router(name="antiflood")

__handlers__ = (
    SetFloodHandler,
    AntifloodStatusHandler,
)


async def __pre_setup__():
    """Register the antiflood middleware and all action configuration handlers."""
    router.message.outer_middleware(AntifloodMiddleware())

    register_action_config_system(
        router,
        module_name="antiflood",
        callback_prefix="antiflood_action",
        wizard_title="Antiflood Action Configuration",
        success_message="Antiflood action updated successfully!",
        get_model_func=get_antiflood_model,
        get_actions_func=get_actions,
        add_action_func=add_action,
        remove_action_func=remove_action,
        command_filter=CMDFilter("setfloodaction"),
        admin_filter=UserRestricting(admin=True),
    )
