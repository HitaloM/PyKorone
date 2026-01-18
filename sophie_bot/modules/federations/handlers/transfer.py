from __future__ import annotations

import json
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, Title

from sophie_bot.db.models.federations import Federation
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.args.fed_id import FedIdArg
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.redis import aredis
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Transfer federation ownership"),
)
@flags.disableable(
    name="transferfed",
)
class TransferOwnershipHandler(SophieMessageHandler):
    """Handler for transferring federation ownership."""

    TRANSFER_KEY_PREFIX = "fed_transfer:"
    TRANSFER_TTL = 300  # 5 minutes

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter(("transferfed", "ftransfer")),
            FeatureFlagFilter("new_feds_transferfed"),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {
            "fed_id": FedIdArg(l_("Federation ID to transfer")),
            "new_owner": TextArg(l_("New owner username or ID")),
        }

    async def handle(self) -> Any:
        """Transfer federation ownership."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id: Federation = self.data["fed_id"]
        new_owner_input: str = self.data["new_owner"]
        user_id = self.event.from_user.id

        # Check if user is the current owner
        if fed_id.creator != user_id:
            await self.event.reply(_("Only the federation owner can transfer ownership."))
            return

        # Parse new owner
        new_owner_id = await self._parse_user_id(
            new_owner_input,
        )
        if not new_owner_id:
            await self.event.reply(_("Invalid user. Please provide a valid username or user ID."))
            return

        # Cannot transfer to self
        if new_owner_id == user_id:
            await self.event.reply(_("You cannot transfer ownership to yourself."))
            return

        # Check if new owner is in the federation
        # For now, allow transfer to any user (can be restricted later,)

        # Create transfer request
        transfer_key = f"{self.TRANSFER_KEY_PREFIX}{fed_id.fed_id}"
        transfer_data = {
            "from_user": user_id,
            "to_user": new_owner_id,
            "fed_id": fed_id.fed_id,
            "fed_name": fed_id.fed_name,
        }

        # Store transfer request in Redis with TTL
        await aredis.set(
            transfer_key,
            json.dumps(transfer_data),
            ex=self.TRANSFER_TTL,
        )

        # TODO: Send confirmation message to new owner (requires user messaging capability,)
        # doc = Doc(
        #     Title(_("🏛 Federation Ownership Transfer"),)
        #     _("You have been offered ownership of federation '{fed_name}'.").format(
        #         fed_name=fed_id.fed_name
        #     )
        #     _("Federation ID: {fed_id}").format(fed_id=fed_id.fed_id)
        #     _("To accept, reply with /accepttransfer {fed_id}").format(fed_id=fed_id.fed_id)
        #     _("This offer expires in 5 minutes.")
        # ,)

        # Confirm to current owner
        confirm_doc = Doc(
            Title(_("🏛 Transfer Request Sent")),
            _("Ownership transfer request sent to user {user_id}.").format(user_id=new_owner_id),
            _("They have 5 minutes to accept with /accepttransfer {fed_id}").format(fed_id=fed_id.fed_id),
        )

        await self.event.reply(str(confirm_doc))

    async def _parse_user_id(self, user_input: str) -> int | None:
        """Parse user ID from username or ID string."""
        # For now, assume it's a user ID
        # TODO: Implement proper user resolution
        try:
            return int(
                user_input,
            )
        except ValueError:
            # TODO: Resolve username to ID
            return None
