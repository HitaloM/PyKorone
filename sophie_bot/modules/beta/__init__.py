from aiogram import Router

from ...filters.admin_rights import UserRestricting
from ...filters.cmd import CMDFilter
from ...filters.message_status import HasArgs
from .handlers.beta_state import set_beta_state, show_beta_state

router = Router(name="error")


def __pre_setup__():
    router.message.register(set_beta_state, CMDFilter("enablebeta"), HasArgs(True), UserRestricting(admin=True))
    router.message.register(show_beta_state, CMDFilter("enablebeta"), UserRestricting(admin=True))
