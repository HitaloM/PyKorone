from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import OptionalArg
from babel.dates import format_date
from stfu_tg import Doc, KeyValue, Title, UserLink

from sophie_bot.db.models import ChatModel
from sophie_bot.db.models.language import LanguageModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.feature_flag import FeatureFlagFilter
from sophie_bot.modules.federations.args.ban import FederationBanUserArg
from sophie_bot.modules.federations.args.fed_id import FedIdArg
from sophie_bot.modules.federations.services.federation import FederationService
from sophie_bot.modules.federations.services.permissions import FederationPermissionService
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Unban a user from the federation"))
@flags.disableable(name="funban")
class FederationUnbanHandler(SophieMessageHandler):
    """Handler for unbanning users from federations."""

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("unfban", "funban")), FeatureFlagFilter("new_feds_funban"))

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, Any]:
        return {
            "fed_id": OptionalArg(
                FedIdArg(l_("Federation ID (optional, uses current chat's federation if not specified)"))
            ),
            "user": FederationBanUserArg(l_("User to unban")),
        }

    async def handle(self) -> Any:
        """Unban user from federation."""
        if not self.event.from_user:
            await self.event.reply(_("This command can only be used by users."))
            return

        fed_id_arg: str | None = self.data.get("fed_id")
        user: ChatModel = self.data["user"]

        # Get federation
        federation = await self._get_federation(fed_id_arg)
        if not federation:
            return

        # Check permissions
        if not await self._check_permissions(federation):
            return

        # Check if user is banned
        ban = await FederationService.is_user_banned(federation.fed_id, user.user_id)
        if not ban:
            await self._reply_user_not_banned()
            return

        # Attempt unban
        was_unbanned, subscription_ban = await FederationService.unban_user(federation.fed_id, user.user_id)
        if not was_unbanned:
            if subscription_ban and subscription_ban.origin_fed:
                await self._handle_subscription_ban_error(subscription_ban, user)
            else:
                await self.event.reply(_("Failed to unban user."))
            return

        # Success - format and send response
        await self._send_success_response(federation, user)

    async def _get_federation(self, fed_id_arg: str | None) -> Any:
        """Get federation from argument or current chat."""
        if fed_id_arg:
            federation = await FederationService.get_federation_by_id(fed_id_arg)
            if not federation:
                await self.event.reply(_("Federation not found."))
                return None
        else:
            # Use current chat's federation
            chat_id = self.connection.id
            federation = await FederationService.get_federation_for_chat(chat_id)
            if not federation:
                await self.event.reply(
                    _("This chat is not in any federation. Use /funban <fed_id> <user> to specify federation.")
                )
                return None
        return federation

    async def _check_permissions(self, federation) -> bool:
        """Check if user has permission to unban in this federation."""
        if not self.event.from_user or not FederationPermissionService.can_ban_in_federation(federation, self.event.from_user.id):
            await self.event.reply(_("You don't have permission to unban users in this federation."))
            return False
        return True

    async def _reply_user_not_banned(self) -> None:
        """Reply when user is not banned."""
        await self.event.reply(_("This user is not banned in this federation."))

    async def _handle_subscription_ban_error(self, subscription_ban, user: ChatModel) -> None:
        """Handle the case where unbanning is blocked due to subscription."""
        origin_fed = await FederationService.get_federation_by_id(subscription_ban.origin_fed)
        if not origin_fed:
            await self.event.reply(_("Cannot unban this user because their ban originated from a subscription."))
            return

        # Format ban date
        locale_name = await LanguageModel.get_locale(self.event.chat.id)
        ban_date = format_date(subscription_ban.time.date(), "short", locale=locale_name)

        # Create detailed error message
        doc = Doc(
            Title(_("🏛 Cannot Unban User")),
            _("This user cannot be unbanned because they are banned in a federation this federation subscribes to."),
            "",
            KeyValue(_("📅 Banned on"), ban_date),
            KeyValue(_("🏛 Federation"), f"{origin_fed.fed_name} ({origin_fed.fed_id})"),
            KeyValue(_("👤 Banned by"), UserLink(subscription_ban.by, f"User {subscription_ban.by}")),
        )

        if subscription_ban.reason:
            doc += KeyValue(_("📝 Reason"), subscription_ban.reason)

        doc += ""
        doc += _("To unban this user, you need to unsubscribe from the parent federation first:")
        doc += f"`/funsub {origin_fed.fed_id}`"

        await self.event.reply(str(doc))

    async def _send_success_response(self, federation, user: ChatModel) -> None:
        """Send success response for unbanning."""
        from_user = self.event.from_user
        if not from_user:
            return

        doc = Doc(
            Title(_("🏛 User Unbanned from Federation")),
            KeyValue(_("Federation"), federation.fed_name),
            KeyValue(_("User"), UserLink(user.user_id, user.first_name or "Unknown")),
            KeyValue(_("Unbanned by"), UserLink(from_user.id, from_user.first_name)),
        )

        await self.event.reply(str(doc))

        # Log the unban
        log_text = _("🏛 User {unbanned_user} has been unbanned from federation by {unbanner}.").format(
            unbanned_user=UserLink(user.user_id, user.first_name or "Unknown").to_html(),
            unbanner=from_user.mention_html(),
        )
        await FederationService.post_federation_log(federation, log_text, self.event.bot)
