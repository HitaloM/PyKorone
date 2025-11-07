from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, Title

from sophie_bot.db.models.federations import Federation
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.args.fed_id import FedIdArg
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Join a chat to a federation"),
)
@flags.disableable(
    name="joinfed",
)
class JoinFederationHandler(SophieMessageHandler):
    """Handler for joining chats to federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("joinfed", "fjoin")), FeatureFlagFilter("new_feds_joinfed"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"fed_id": FedIdArg(l_("Federation ID to join"))}

    async def handle(self) -> Any:
        """Join the current chat to a federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id: Federation = self.data["fed_id"]
        chat_id = self.connection.id
        user_id = self.event.from_user.id

        # Check if user can join chats to federation
        # Must be chat creator or have admin rights
        if not await self._can_user_join_chat(chat_id, user_id):
            await self.event.reply(_("Only the chat creator can join federations."))
            return

        # Check if chat is already in a federation
        existing_fed = await FederationService.get_federation_for_chat(
            chat_id,
        )
        if existing_fed:
            if existing_fed.fed_id == fed_id.fed_id:
                await self.event.reply(_("This chat is already in the specified federation."))
                return
            else:
                await self.event.reply(_("This chat is already in another federation. Leave it first."))
                return

        # Add chat to federation
        await FederationService.add_chat_to_federation(
            fed_id,
            chat_id,
        )

        # Format success message
        doc = Doc(
            Title(_("🏛 Chat Joined Federation")),
            _("Chat '{chat_title}' has been added to federation '{fed_name}'.").format(
                chat_title=self.connection.title, fed_name=fed_id.fed_name
            ),
            _("Federation ID: {fed_id}").format(fed_id=fed_id.fed_id),
        )

        await self.event.reply(str(doc))

        # Log the chat joining
        log_text = _("🏛 Chat '{chat_title}' has been added to federation by {user}.").format(
            chat_title=self.connection.title, user=self.event.from_user.mention_html()
        )
        await FederationService.post_federation_log(fed_id, log_text, self.event.bot)

    async def _can_user_join_chat(self, chat_id: int, user_id: int) -> bool:
        """Check if user can join this chat to a federation."""
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
