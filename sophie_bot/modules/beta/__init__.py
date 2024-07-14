from aiogram import Router

from ...filters.admin_rights import UserRestricting
from ...filters.cmd import CMDFilter
from ...filters.message_status import HasArgs
from ...filters.user_status import IsOP
from .handlers.beta_state import set_preferred_mode, show_beta_state
from .handlers.op_settings import ResetBetaChats, SetBetaPercentage
from .stats import beta_stats

router = Router(name="beta")


def __pre_setup__():
    router.message.register(set_preferred_mode, CMDFilter("enablebeta"), HasArgs(True), UserRestricting(admin=True))
    router.message.register(show_beta_state, CMDFilter("enablebeta"), UserRestricting(admin=True))

    router.message.register(SetBetaPercentage, CMDFilter("op_setbeta"), IsOP(True))
    router.message.register(ResetBetaChats, CMDFilter("op_resetbeta"), IsOP(True))


__stats__ = beta_stats
