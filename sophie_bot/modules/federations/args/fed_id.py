from typing import Optional
from ass_tg.exceptions import ArgStrictError
from ass_tg.types import TextArg
from stfu_tg import Code

from sophie_bot.db.models.federations import Federation
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class FedIdArg(TextArg):
    """Argument type for federation IDs with validation and lookup."""

    def __init__(self, description: Optional[LazyProxy] = None):
        super().__init__(description or l_("Federation ID"))

    async def value(self, text: str) -> Optional[Federation]:
        """Parse and validate federation ID, return Federation model."""
        # Validate format (exactly 4 hyphens)
        if text.count("-") != 4:
            raise ArgStrictError(_("Invalid federation ID format. Federation IDs must contain exactly 4 hyphens."))

        # Lookup federation
        federation = await Federation.find_one(Federation.fed_id == text)
        if not federation:
            raise ArgStrictError(_("Federation with ID {fed_id} not found.").format(fed_id=Code(text)))

        return federation

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Federation ID (format: xxxx-xxxx-xxxx-xxxx)"), l_("Federation IDs")

    @property
    def examples(self) -> Optional[dict[str, Optional[LazyProxy]]]:
        return {"a1b2-c3d4-e5f6-g7h8": l_("Federation ID example")}
