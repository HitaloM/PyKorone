from __future__ import annotations

from typing import Any

from beanie import PydanticObjectId

from .base import ActionConfigWizardABC
from .renderer import WizardRenderer


class ActionConfigWizardMixin(ActionConfigWizardABC):
    """Mixin providing concrete implementation for the wizard handler."""

    async def handle(self) -> Any:
        """Handle the main command to show action configuration (via renderer)."""
        chat_tid: PydanticObjectId = self.connection.db_model.iid  # type: ignore
        state = self.data.get("state")
        html, markup = await WizardRenderer.render_home_page(
            self,
            chat_iid=chat_tid,
            chat_title=self.connection.title,
            state=state,
        )
        await self.event.reply(html, reply_markup=markup)
