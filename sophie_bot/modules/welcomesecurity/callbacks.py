from typing import Literal

from aiogram.filters.callback_data import CallbackData


class WelcomeSecurityMoveCB(CallbackData, prefix="ws_move_right"):
    direction: Literal["left", "right"]


class WelcomeSecurityConfirmCB(CallbackData, prefix="ws_confirm"):
    pass


class WelcomeSecurityRulesAgreeCB(CallbackData, prefix="ws_rules_agree"):
    pass
