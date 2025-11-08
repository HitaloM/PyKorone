from typing import Literal

from aiogram.filters.callback_data import CallbackData


class WelcomeSecurityMoveCB(CallbackData, prefix="ws_move_right"):
    direction: Literal["left", "right"]
    chat_iid: str | None = None
    is_join_request: bool = False


class WelcomeSecurityConfirmCB(CallbackData, prefix="ws_confirm"):
    chat_iid: str | None = None
    is_join_request: bool = False


class WelcomeSecurityRulesAgreeCB(CallbackData, prefix="ws_rules_agree"):
    chat_iid: str | None = None
    is_join_request: bool = False
