from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from stfu_tg import Doc, Title

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Sets the Federation logs channel"))
@flags.disableable(name="fsetlog")
class SetFederationLogHandler(SophieMessageHandler):
    """Handler for setting federation log channel."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("fsetlog", "setfedlog")), FeatureFlagFilter("new_feds_setlog"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, Any]:
        return {}

    async def handle(self) -> Any:
        """Set federation log channel."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        # Get the current chat
        chat_id = self.connection.tid

        # Get federation for this chat
        federation = await FederationService.get_federation_for_chat(chat_id)
        if not federation:
            await self.event.reply(_("This chat is not in any federation."))
            return

        # Check if user is federation owner
        if federation.creator != self.event.from_user.id:
            await self.event.reply(_("Only the federation owner can set the log channel."))
            return

        # Check if log channel is already set
        if federation.log_chat_id:
            await self.event.reply(
                _("This federation already has a log channel set. Use /funsetlog to remove it first.")
            )
            return

        # For channels, we need to check if bot can post
        if self.connection.type == "channel":
            # Check if bot has permission to post in this channel
            try:
                bot_member = await self.event.bot.get_chat_member(chat_id, self.event.bot.id)
                if not bot_member.can_post_messages:
                    await self.event.reply(_("I don't have permission to post messages in this channel."))
                    return
            except Exception:
                await self.event.reply(_("Unable to verify permissions in this channel."))
                return

        # Set the log channel
        await FederationService.set_federation_log_channel(federation, chat_id)

        # Send confirmation
        doc = Doc(
            Title(_("🏛 Federation Log Channel Set")),
            _("Log channel has been set for federation '{name}'.").format(name=federation.fed_name),
            _("All federation actions will now be logged here."),
        )
        await self.event.reply(str(doc))

        # Post log message
        log_text = _("🏛 Federation '{name}' log channel has been set to this chat.").format(name=federation.fed_name)
        await FederationService.post_federation_log(federation, log_text, self.event.bot)


@flags.help(description=l_("Removes the Federation logs channel"))
@flags.disableable(name="funsetlog")
class UnsetFederationLogHandler(SophieMessageHandler):
    """Handler for removing federation log channel."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("funsetlog", "unsetfedlog")), FeatureFlagFilter("new_feds_unsetlog"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, Any]:
        return {}

    async def handle(self) -> Any:
        """Remove federation log channel."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        # Get the current chat
        chat_id = self.connection.tid

        # Get federation for this chat
        federation = await FederationService.get_federation_for_chat(chat_id)
        if not federation:
            await self.event.reply(_("This chat is not in any federation."))
            return

        # Check if user is federation owner
        if federation.creator != self.event.from_user.id:
            await self.event.reply(_("Only the federation owner can remove the log channel."))
            return

        # Check if log channel is set
        if not federation.log_chat_id:
            await self.event.reply(_("This federation doesn't have a log channel set."))
            return

        # Post log message before removing
        log_text = _("🏛 Federation '{name}' log channel has been removed.").format(name=federation.fed_name)
        await FederationService.post_federation_log(federation, log_text, self.event.bot)

        # Remove the log channel
        await FederationService.remove_federation_log_channel(federation)

        # Send confirmation
        doc = Doc(
            Title(_("🏛 Federation Log Channel Removed")),
            _("Log channel has been removed for federation '{name}'.").format(name=federation.fed_name),
        )
        await self.event.reply(str(doc))
