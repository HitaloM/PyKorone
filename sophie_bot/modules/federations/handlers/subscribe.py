from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, KeyValue, Title

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.federations.services.permissions import FederationPermissionService
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Subscribe federation to another federation"),
)
@flags.disableable(
    name="fsub",
)
class SubscribeFederationHandler(SophieMessageHandler):
    """Handler for subscribing federations to other federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("fsub",)), FeatureFlagFilter("new_feds_fsub"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"fed_id": TextArg(l_("Federation ID to subscribe to"))}

    async def handle(self) -> Any:
        """Subscribe federation to another federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        target_fed_id: str = self.data["fed_id"]

        # Get federation for current chat
        federation = await FederationService.get_federation_for_chat(self.event.chat.id)
        if not federation:
            await self.event.reply(_("This chat is not in a federation."))
            return

        # Check permissions
        if not FederationPermissionService.is_federation_owner(federation, self.event.from_user.id):
            await self.event.reply(_("Only federation owners can manage subscriptions."))
            return

        # Validate target federation ID format
        if not self._is_valid_fed_id(target_fed_id):
            await self.event.reply(_("Invalid federation ID format."))
            return

        # Subscribe to federation
        success = await FederationService.subscribe_to_federation(federation, target_fed_id)
        if not success:
            target_fed = await FederationService.get_federation_by_id(target_fed_id)
            if not target_fed:
                await self.event.reply(_("Federation not found."))
                return

            doc = Doc(
                Title(_("🏛 Subscription Failed")),
                _("Federation '{name}' is already subscribed to '{name2}'.").format(
                    name=federation.fed_name,
                    name2=target_fed.fed_name,
                ),
            )
            await self.event.reply(str(doc))
            return

        # Get target federation for logging
        target_fed = await FederationService.get_federation_by_id(target_fed_id)
        if not target_fed:
            await self.event.reply(_("Federation not found."))
            return

        # Format response using STFU
        doc = Doc(
            Title(_("🏛 Federation Subscribed")),
            KeyValue(_("Federation"), federation.fed_name),
            KeyValue(_("Subscribed to"), target_fed.fed_name),
        )

        await self.event.reply(str(doc))

        # Log the subscription
        log_text = _("🏛 Federation '{fed_name}' ({fed_id}) subscribed to '{target_fed_name}' ({target_fed_id})").format(
            fed_name=federation.fed_name,
            fed_id=federation.fed_id,
            target_fed_name=target_fed.fed_name,
            target_fed_id=target_fed.fed_id,
        )
        await FederationService.post_federation_log(federation, log_text, bot)

        # Log the subscription
        await FederationService.post_federation_log(
            federation,
            _("Federation '{fed_name}' ({fed_id}) subscribed to '{target_fed_name}' ({target_fed_id})").format(
                fed_name=federation.fed_name,
                fed_id=federation.fed_id,
                target_fed_name=target_fed.fed_name,
                target_fed_id=target_fed.fed_id,
            ),
            bot,
        )

    @staticmethod
    def _is_valid_fed_id(fed_id: str) -> bool:
        """Validate federation ID format (4 groups of 4 characters separated by hyphens)."""
        parts = fed_id.split("-")
        return len(parts) == 4 and all(len(part) == 4 for part in parts)


@flags.help(
    description=l_("Unsubscribe federation from another federation"),
)
@flags.disableable(
    name="funsub",
)
class UnsubscribeFederationHandler(SophieMessageHandler):
    """Handler for unsubscribing federations from other federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("funsub",)), FeatureFlagFilter("new_feds_funsub"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"fed_id": TextArg(l_("Federation ID to unsubscribe from"))}

    async def handle(self) -> Any:
        """Unsubscribe federation from another federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id: str = self.data["fed_id"]

        # Get federation for current chat
        federation = await FederationService.get_federation_for_chat(self.event.chat.id)
        if not federation:
            await self.event.reply(_("This chat is not in a federation."))
            return

        # Check permissions
        if not FederationPermissionService.is_federation_owner(federation, self.event.from_user.id):
            await self.event.reply(_("Only federation owners can manage subscriptions."))
            return

        # Unsubscribe from federation
        success = await FederationService.unsubscribe_from_federation(federation, fed_id)
        if not success:
            target_fed = await FederationService.get_federation_by_id(fed_id)
            if not target_fed:
                await self.event.reply(_("Federation not found."))
                return

            doc = Doc(
                Title(_("🏛 Unsubscription Failed")),
                _("Federation '{name}' is not subscribed to '{name2}'.").format(
                    name=federation.fed_name,
                    name2=target_fed.fed_name,
                ),
            )
            await self.event.reply(str(doc))
            return

        # Get target federation for response
        target_fed = await FederationService.get_federation_by_id(fed_id)
        if not target_fed:
            await self.event.reply(_("Federation not found."))
            return

        # Format response using STFU
        doc = Doc(
            Title(_("🏛 Federation Unsubscribed")),
            KeyValue(_("Federation"), federation.fed_name),
            KeyValue(_("Unsubscribed from"), target_fed.fed_name),
        )

        await self.event.reply(str(doc))

        # Log the unsubscription
        log_text = _(
            "🏛 Federation '{fed_name}' ({fed_id}) unsubscribed from '{target_fed_name}' ({target_fed_id})"
        ).format(
            fed_name=federation.fed_name,
            fed_id=federation.fed_id,
            target_fed_name=target_fed.fed_name,
            target_fed_id=target_fed.fed_id,
        )
        await FederationService.post_federation_log(federation, log_text, bot)
