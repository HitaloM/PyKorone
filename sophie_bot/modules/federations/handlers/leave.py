from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Doc, Title

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Leave a federation"),
)
@flags.disableable(
    name="leavefed",
)
class LeaveFederationHandler(SophieMessageHandler):
    """Handler for leaving federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("leavefed", "fleave")), FeatureFlagFilter("new_feds_leavefed"))

    async def handle(self) -> Any:
        """Leave the current chat from its federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        chat_id = self.connection.id
        user_id = self.event.from_user.id

        # Check if user can leave chats from federation
        # Must be chat creator or have admin rights
        if not await self._can_user_leave_chat(chat_id, user_id):
            await self.event.reply(_("Only the chat creator can leave federations."))
            return

        # Check if chat is in a federation
        federation = await FederationService.get_federation_for_chat(
            chat_id,
        )
        if not federation:
            await self.event.reply(_("This chat is not in any federation."))
            return

        # Remove chat from federation
        await FederationService.remove_chat_from_federation(federation, chat_id)

        # Format success message
        doc = Doc(
            Title(_("🏛 Chat Left Federation")),
            _("Chat '{chat_title}' has left federation '{fed_name}'.").format(
                chat_title=self.connection.title, fed_name=federation.fed_name
            ),
            _("Federation ID: {fed_id}").format(fed_id=federation.fed_id),
        )

        await self.event.reply(str(doc))

        # Log the chat leaving
        log_text = _("🏛 Chat '{chat_title}' has left federation by {user}.").format(
            chat_title=self.connection.title, user=self.event.from_user.mention_html()
        )
        await FederationService.post_federation_log(federation, log_text, self.event.bot)

    async def _can_user_leave_chat(self, chat_id: int, user_id: int) -> bool:
        """Check if user can leave this chat from a federation."""
        # For now, require admin rights (can be extended to check creator status,)
        # This follows the pattern from legacy code
        from sophie_bot.modules.legacy_modules.utils.user_details import is_chat_creator

        try:
            return await is_chat_creator(
                self.event,
                chat_id,
                user_id,
            )
        except Exception:
            # Fallback to checking admin rights
            return False
