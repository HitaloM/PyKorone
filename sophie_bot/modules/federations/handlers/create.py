from __future__ import annotations

from typing import Any
import uuid

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import Doc, Title

from sophie_bot.db.models.federations import Federation
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(
    description=l_("Create a new federation"),
)
@flags.disableable(
    name="newfed",
)
class CreateFederationHandler(SophieMessageHandler):
    """Handler for creating new federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("newfed", "fnew")), FeatureFlagFilter("new_feds_newfed"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {"name": TextArg(l_("Federation name"))}

    async def handle(self) -> Any:
        """Create a new federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        name: str = self.data["name"]

        # Validate name length
        from sophie_bot.modules.federations.config import MAX_FEDERATION_NAME_LENGTH

        if len(name) > MAX_FEDERATION_NAME_LENGTH:
            await self.event.reply(
                _("Federation name too long. Maximum length is {max_length} characters.").format(
                    max_length=MAX_FEDERATION_NAME_LENGTH
                )
            )
            return

        # Check if user can create federation
        if not await FederationService._can_user_create_federation(self.event.from_user.id):
            await self.event.reply(_("You have reached the maximum number of federations you can create."))
            return

        # Check name uniqueness
        if await Federation.find_one(Federation.fed_name == name):
            await self.event.reply(_("A federation with this name already exists."))
            return

        # Create federation
        federation = Federation(fed_name=name, fed_id=str(uuid.uuid4()), creator=self.event.from_user.id)
        await federation.insert()

        # Format success message
        doc = Doc(
            Title(
                _("🏛 Federation Created"),
            ),
            _("Federation '{name}' has been created successfully!").format(name=federation.fed_name),
            _("Federation ID: {fed_id}").format(fed_id=federation.fed_id),
            _("You are the owner of this federation."),
        )

        await self.event.reply(str(doc))

        # Log the federation creation
        log_text = _("🏛 Federation '{name}' has been created by {user}.").format(
            name=federation.fed_name, user=self.event.from_user.mention_html()
        )
        await FederationService.post_federation_log(federation, log_text, self.event.bot)
