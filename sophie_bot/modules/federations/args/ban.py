from typing import Optional

from ass_tg.types import TextArg

from sophie_bot.args.users import SophieUserArg
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import lazy_gettext as l_


# Use SophieUserArg directly for user argument
FederationBanUserArg = SophieUserArg


class FederationBanReasonArg(TextArg):
    """Argument for ban reason."""

    def __init__(self, description: Optional[LazyProxy] = None):
        super().__init__(description or l_("Reason (optional)"))

    async def value(self, text: str) -> Optional[str]:
        """Parse reason, return None if empty."""
        reason = text.strip()
        return reason if reason else None
