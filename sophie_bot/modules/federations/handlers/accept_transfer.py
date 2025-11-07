from __future__ import annotations

import json
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, Title

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Accept federation ownership transfer"))
@flags.disableable(name="accepttransfer")
class AcceptTransferHandler(SophieMessageHandler):
    """Handler for accepting federation ownership transfers."""

    TRANSFER_KEY_PREFIX = "fed_transfer:"

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("accepttransfer",)), FeatureFlagFilter("new_feds_accepttransfer"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"fed_id": TextArg(l_("Federation ID to accept transfer for"))}

    async def handle(self) -> Any:
        """Accept federation ownership transfer."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id_input: str = self.data["fed_id"]
        user_id = self.event.from_user.id

        # Get transfer request from Redis
        transfer_key = f"{self.TRANSFER_KEY_PREFIX}{fed_id_input}"
        transfer_data_raw = await aredis.get(
            transfer_key,
        )

        if not transfer_data_raw:
            await self.event.reply(_("No pending transfer request found for this federation."))
            return

        try:
            transfer_data = json.loads(
                transfer_data_raw,
            )
        except json.JSONDecodeError:
            await self.event.reply(_("Invalid transfer request data."))
            return

        # Validate transfer data
        if transfer_data.get("to_user") != user_id:
            await self.event.reply(_("This transfer request is not for you."))
            return

        if transfer_data.get("fed_id") != fed_id_input:
            await self.event.reply(_("Federation ID mismatch."))
            return

        # Get federation
        federation = await FederationService.get_federation_by_id(
            fed_id_input,
        )
        if not federation:
            await self.event.reply(_("Federation not found."))
            return

        # Verify current owner
        if federation.creator != transfer_data.get("from_user"):
            await self.event.reply(_("Transfer request is outdated. The federation owner has changed."))
            return

        # Transfer ownership
        await FederationService.update_federation(
            federation,
            {"creator": user_id},
        )

        # Clean up transfer request
        await aredis.delete(
            transfer_key,
        )

        # Format success message
        doc = Doc(
            Title(
                _("🏛 Ownership Transferred"),
            ),
            _("You are now the owner of federation '{fed_name}'.").format(fed_name=federation.fed_name),
            _("Federation ID: {fed_id}").format(fed_id=federation.fed_id),
        )

        await self.event.reply(str(doc))
