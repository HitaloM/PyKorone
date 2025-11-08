from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import OptionalArg
from stfu_tg import Doc, KeyValue, Title

from sophie_bot.db.models.chat import ChatType
from sophie_bot.db.models.federations import Federation
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.args.fed_id import FedIdArg
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Get information about a federation"))
@flags.disableable(name="fedinfo")
class FederationInfoHandler(SophieMessageHandler):
    """Handler for getting federation information."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("fedinfo", "finfo")), FeatureFlagFilter("new_feds_finfo"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, Any]:
        return {"fed_id": OptionalArg(FedIdArg(l_("Federation ID to get info about (optional)")))}

    async def handle(self) -> Any:
        """Get information about a federation."""
        fed_id_arg: Federation | None = self.data.get("fed_id")

        if fed_id_arg:
            # Show info for specific federation
            await self._show_federation_info(fed_id_arg)
        elif self.connection.type == ChatType.private:
            # In private chat, show all user's federations
            await self._show_user_federations()
        else:
            # In group chat, show current chat's federation
            await self._show_chat_federation()

    async def _show_federation_info(self, federation: Federation) -> None:
        """Show information about a specific federation."""
        chat_count = await FederationService.get_federation_chat_count(federation.fed_id)
        ban_count = await FederationService.get_federation_ban_count(federation.fed_id)

        doc = Doc(
            Title(_("🏛 Federation Information")),
            KeyValue(_("Name"), federation.fed_name),
            KeyValue(_("ID"), federation.fed_id),
            KeyValue(_("Owner"), federation.creator),
            KeyValue(_("Chats"), chat_count),
            KeyValue(_("Banned users"), ban_count),
        )

        # Add subscription information
        if federation.subscribed:
            subscription_list = []
            for sub_fed_id in federation.subscribed:
                sub_fed = await FederationService.get_federation_by_id(sub_fed_id)
                if sub_fed:
                    subscription_list.append(f"• {sub_fed.fed_name} (`{sub_fed.fed_id}`)")
                else:
                    subscription_list.append(f"• Unknown (`{sub_fed_id}`)")

            doc += KeyValue(_("Subscribed to"), "\n".join(subscription_list))

        await self.event.reply(str(doc))

    async def _show_user_federations(self) -> None:
        """Show all federations owned by the user."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        user_id = self.event.from_user.id
        federations = await FederationService.get_federations_by_creator(user_id)

        if not federations:
            await self.event.reply(_("You don't own any federations."))
            return

        if len(federations) == 1:
            # Show detailed info for single federation
            await self._show_federation_info(federations[0])
            return

        # Show list of federations with guidance for multiple federations
        from stfu_tg import VList  # Add this import at the top of the file

        federation_list = VList(*(f"• {federation.fed_name} (ID: `{federation.fed_id}`)" for federation in federations))

        doc = Doc(
            Title(_("🏛 Your Federations")),
            _("You own {count} federations:").format(count=len(federations)),
            federation_list,
            "",
            _("To get detailed information about a specific federation, use:"),
            _("`/finfo <federation_id>`"),
        )
        await self.event.reply(str(doc))

    async def _show_chat_federation(self) -> None:
        """Show federation information for the current chat."""
        chat_id = self.connection.id
        federation = await FederationService.get_federation_for_chat(chat_id)

        if not federation:
            await self.event.reply(_("This chat is not in any federation."))
            return

        await self._show_federation_info(federation)
