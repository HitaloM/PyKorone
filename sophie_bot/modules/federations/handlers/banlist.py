from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import OptionalArg
from stfu_tg import Doc, KeyValue, Section, Title, UserLink

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.args.fed_id import FedIdArg
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.federations.services.permissions import FederationPermissionService
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Show list of banned users in federation"))
@flags.disableable(name="fbanlist")
class FederationBanListHandler(SophieMessageHandler):
    """Handler for showing federation ban lists."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("fbanlist", "exportfbans", "fexport")), FeatureFlagFilter("new_feds_fbanlist"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, Any]:
        return {
            "fed_id": OptionalArg(
                FedIdArg(l_("Federation ID (optional, uses current chat's federation if not specified)"))
            ),
        }

    async def handle(self) -> Any:
        """Show list of banned users in federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id_arg: str | None = self.data.get("fed_id")

        # Determine federation
        if fed_id_arg:
            federation = await FederationService.get_federation_by_id(fed_id_arg)
            if not federation:
                await self.event.reply(_("Federation not found."))
                return
        else:
            # Use current chat's federation
            chat_id = self.connection.tid
            federation = await FederationService.get_federation_for_chat(chat_id)
            if not federation:
                await self.event.reply(
                    _("This chat is not in any federation. Use /fbanlist <fed_id> to specify federation.")
                )
                return

        # Permission check - federation admin or owner
        if not FederationPermissionService.can_ban_in_federation(federation, self.event.from_user.id):
            await self.event.reply(_("You don't have permission to view ban lists in this federation."))
            return

        # Get banned users
        bans = await FederationService.get_federation_bans(federation.fed_id)

        if not bans:
            doc = Doc(
                Title(_("🏛 Federation Ban List")),
                KeyValue(_("Federation"), federation.fed_name),
                _("No users are currently banned in this federation."),
            )
            await self.event.reply(str(doc))
            return

        # Format ban list
        ban_sections = []
        for ban in bans:
            # Get user info - we need to fetch user details
            try:
                from sophie_bot.db.models import ChatModel

                user = await ChatModel.find_user(ban.user_id)
                user_name = user.first_name or "Unknown" if user else "Unknown"
            except Exception:
                user_name = "Unknown"

            ban_info = [
                KeyValue(_("User"), UserLink(ban.user_id, user_name)),
                KeyValue(_("Banned by"), UserLink(ban.by, "Unknown")),
                KeyValue(_("Date"), ban.time.strftime("%Y-%m-%d %H:%M UTC")),
            ]
            if ban.reason:
                ban_info.append(KeyValue(_("Reason"), ban.reason))

            ban_sections.append(Section(*ban_info, title=user_name))

        doc = Doc(
            Title(_("🏛 Federation Ban List")),
            KeyValue(_("Federation"), federation.fed_name),
            KeyValue(_("Total bans"), len(bans)),
            *ban_sections,
        )

        await self.event.reply(str(doc))
