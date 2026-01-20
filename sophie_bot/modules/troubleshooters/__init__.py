from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.admin_rights import UserRestricting
from ...filters.cmd import CMDFilter
from ...filters.message_status import HasArgs
from ...filters.user_status import IsOP
from .handlers.admincache import ResetAdminCache
from .handlers.beta_state import set_preferred_mode, show_beta_state
from .handlers.cancel import CancelState
from .handlers.cancel_callback import CallbackActionCancelHandler, CancelCallbackHandler, TypedCancelCallbackHandler
from .handlers.op_settings import ResetBetaChats, SetBetaPercentage
from .stats import beta_stats

router = Router(name="troubleshooters")

__module_name__ = l_("Troubleshooters")
__module_emoji__ = "🧰"
__module_info__ = l_("Small commands for fixing problems and issues")


__stats__ = beta_stats

__handlers__ = (CancelCallbackHandler, TypedCancelCallbackHandler, CallbackActionCancelHandler, ResetAdminCache)


async def __pre_setup__():
    # Beta
    router.message.register(set_preferred_mode, CMDFilter("enablebeta"), HasArgs(True), UserRestricting(admin=True))
    router.message.register(show_beta_state, CMDFilter("enablebeta"), UserRestricting(admin=True))

    router.message.register(SetBetaPercentage, CMDFilter("op_setbeta"), IsOP(True))
    router.message.register(ResetBetaChats, CMDFilter("op_resetbeta"), IsOP(True))

    # Troubleshooting
    router.message.register(CancelState, CMDFilter("cancel"))
