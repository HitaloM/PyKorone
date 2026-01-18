from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import OptionalArg
from stfu_tg import Doc, KeyValue, Title, UserLink

from sophie_bot.config import CONFIG
from sophie_bot.db.models import ChatModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.args.ban import FederationBanReasonArg, FederationBanUserArg
from sophie_bot.modules.federations.args.fed_id import FedIdArg
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.federations.services.permissions import FederationPermissionService
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Ban a user from the federation"))
@flags.disableable(name="fban")
class FederationBanHandler(SophieMessageHandler):
    """Handler for banning users from federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("fban", "sfban")), FeatureFlagFilter("new_feds_fban"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, Any]:
        return {
            "fed_id": OptionalArg(
                FedIdArg(l_("Federation ID (optional, uses current chat's federation if not specified)"))
            ),
            "user": FederationBanUserArg(l_("User to ban")),
            "reason": OptionalArg(FederationBanReasonArg()),
        }

    async def handle(self) -> Any:
        """Ban user from federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id_arg: str | None = self.data.get("fed_id")
        user: ChatModel = self.data["user"]
        reason: str | None = self.data.get("reason")

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
                    _("This chat is not in any federation. Use /fban <fed_id> <user> to specify federation.")
                )
                return

        # Permission check
        if not FederationPermissionService.can_ban_in_federation(federation, self.event.from_user.id):
            await self.event.reply(_("You don't have permission to ban users in this federation."))
            return

        # Validation
        if user.user_id in CONFIG.operators:
            await self.event.reply(_("Cannot ban bot operators."))
            return

        if user.user_id == self.event.from_user.id:
            await self.event.reply(_("You cannot ban yourself."))
            return

        if user.user_id == CONFIG.bot_id:
            await self.event.reply(_("Cannot ban the bot."))
            return

        if user.user_id == federation.creator:
            await self.event.reply(_("Cannot ban the federation owner."))
            return

        # Check if user is federation admin
        if federation.admins and user.user_id in federation.admins:
            await self.event.reply(_("Cannot ban federation administrators."))
            return

        # Ban user
        await FederationService.ban_user(federation, user.user_id, self.event.from_user.id, reason)

        # Format response
        silent = self.event.text and self.event.text.startswith("/sfban")
        doc = Doc(
            Title(_("🏛 User Banned from Federation")),
            KeyValue(_("Federation"), federation.fed_name),
            KeyValue(_("User"), UserLink(user.user_id, user.first_name or "Unknown")),
            KeyValue(_("Banned by"), UserLink(self.event.from_user.id, self.event.from_user.first_name)),
        )
        if reason:
            doc += KeyValue(_("Reason"), reason)

        await self.event.reply(str(doc))

        # Log the ban
        log_text = _("🏛 User {banned_user} has been banned from federation by {banner}.").format(
            banned_user=UserLink(user.user_id, user.first_name or "Unknown").to_html(),
            banner=self.event.from_user.mention_html(),
        )
        if reason:
            log_text += _(" Reason: {reason}").format(reason=reason)
        await FederationService.post_federation_log(federation, log_text, self.event.bot)

        # TODO: Send ban notifications to federation chats (non-silent only)
        if not silent:
            # Implementation for notifying chats would go here
            pass
