from __future__ import annotations

from typing import Optional

from aiogram.filters.callback_data import CallbackData


class ACWCoreCallback(CallbackData, prefix="acw"):
    """Core callback for Action Config Wizard.

    Fields:
    - mod: module-specific callback prefix (used to scope handlers per module)
    - op: operation, e.g., add | remove | configure | back | done | cancel | select
    - name: optional payload (e.g., action name to configure/remove/select)
    """

    mod: str
    op: str
    name: Optional[str] = None


class ACWSettingCallback(CallbackData, prefix="acw_setting"):
    """Settings callback for Action Config Wizard.

    Fields:
    - mod: module-specific callback prefix (used to scope handlers per module)
    - name: action name
    - setting: setting identifier within the action
    """

    mod: str
    name: str
    setting: str
