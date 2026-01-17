from aiogram import Router

from sophie_bot.modules.restrictions.actions.ban import BanModernAction
from sophie_bot.modules.restrictions.actions.kick import KickModernAction
from sophie_bot.modules.restrictions.actions.mute import MuteModernAction
from sophie_bot.modules.restrictions.handlers import (
    BanUserHandler,
    KickUserHandler,
    MuteUserHandler,
    TempBanUserHandler,
    TempMuteUserHandler,
    UnbanUserHandler,
    UnmuteUserHandler,
)
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Restrictions")
__module_emoji__ = "🛑"

router = Router(name="restrictions")

__modern_actions__ = (KickModernAction, BanModernAction, MuteModernAction)

__handlers__ = (
    KickUserHandler,
    BanUserHandler,
    TempBanUserHandler,
    MuteUserHandler,
    TempMuteUserHandler,
    UnmuteUserHandler,
    UnbanUserHandler,
)
