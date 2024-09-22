from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.admin_rights import UserRestricting
from ...filters.cmd import CMDFilter
from ...filters.message_status import HasArgs
from ...filters.user_status import IsOP
from .handlers.beta_state import set_preferred_mode, show_beta_state
from .handlers.op_settings import ResetBetaChats, SetBetaPercentage
from .stats import beta_stats

router = Router(name="beta")

__module_name__ = l_("Beta")
__module_emoji__ = "🐞"
__module_description__ = l_(
    """Controls the current Sophie mode.
Please note that Beta mode can have bugs and issues. If you encounter any problems please report it to the support chat."""
)


def __pre_setup__():
    router.message.register(set_preferred_mode, CMDFilter("enablebeta"), HasArgs(True), UserRestricting(admin=True))
    router.message.register(show_beta_state, CMDFilter("enablebeta"), UserRestricting(admin=True))

    router.message.register(SetBetaPercentage, CMDFilter("op_setbeta"), IsOP(True))
    router.message.register(ResetBetaChats, CMDFilter("op_resetbeta"), IsOP(True))


__stats__ = beta_stats
