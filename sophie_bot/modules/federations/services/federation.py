from datetime import datetime
from typing import List, Optional
import uuid

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from sophie_bot.db.models.federations import Federation, FederationBan
from sophie_bot.config import CONFIG
from sophie_bot.modules.federations.config import MAX_FEDERATION_NAME_LENGTH, MAX_FEDERATIONS_PER_USER


class FederationService:
    """Business logic for federation operations."""

    @staticmethod
    async def create_federation(name: str, creator: int) -> Federation | None:
        """Create a new federation. Returns None if validation fails."""
        # Validate name
        if len(name) > MAX_FEDERATION_NAME_LENGTH:
            return None

        # Check if user can create federation
        if not await FederationService._can_user_create_federation(creator):
            return None

        # Check name uniqueness
        if await Federation.find_one(Federation.fed_name == name):
            return None

        # Create federation
        federation = Federation(fed_name=name, fed_id=str(uuid.uuid4()), creator=creator)
        await federation.insert()

        return federation

    @staticmethod
    async def get_federation_by_id(fed_id: str) -> Optional[Federation]:
        """Get federation by ID."""
        return await Federation.find_one(Federation.fed_id == fed_id)

    @staticmethod
    async def get_federation_by_creator(creator: int) -> Optional[Federation]:
        """Get federation created by user."""
        return await Federation.find_one(Federation.creator == creator)

    @staticmethod
    async def get_federations_by_creator(creator: int) -> list[Federation]:
        """Get all federations created by user."""
        return await Federation.find(Federation.creator == creator).to_list()

    @staticmethod
    async def get_federation_for_chat(chat_id: int) -> Optional[Federation]:
        """Get federation that contains the chat."""
        return await Federation.find_one(Federation.chats == chat_id)

    @staticmethod
    async def update_federation(federation: Federation, updates: dict) -> Federation:
        """Update federation with new data."""
        for key, value in updates.items():
            setattr(federation, key, value)
        await federation.save()
        return federation

    @staticmethod
    async def delete_federation(federation: Federation) -> None:
        """Delete federation and all related data."""
        # Delete federation bans
        from sophie_bot.db.models.federations import FederationBan

        await FederationBan.find(FederationBan.fed_id == federation.fed_id).delete()

        # Delete federation
        await federation.delete()

    @staticmethod
    async def add_chat_to_federation(federation: Federation, chat_id: int) -> None:
        """Add chat to federation."""
        if federation.chats is None:
            federation.chats = []
        if chat_id not in federation.chats:
            federation.chats.append(chat_id)
            await federation.save()

    @staticmethod
    async def remove_chat_from_federation(federation: Federation, chat_id: int) -> None:
        """Remove chat from federation."""
        if federation.chats is None:
            return
        if chat_id in federation.chats:
            federation.chats.remove(chat_id)
            await federation.save()

    @staticmethod
    async def get_federation_chat_count(fed_id: str) -> int:
        """Get number of chats in federation."""
        federation = await FederationService.get_federation_by_id(fed_id)
        if not federation or not federation.chats:
            return 0
        return len(federation.chats)

    @staticmethod
    async def get_federation_ban_count(fed_id: str) -> int:
        """Get number of banned users in federation."""
        from sophie_bot.db.models.federations import FederationBan

        return await FederationBan.find(FederationBan.fed_id == fed_id).count()

    @staticmethod
    async def ban_user(
        federation: Federation, user_id: int, by_user: int, reason: Optional[str] = None
    ) -> FederationBan:
        """Ban user from federation and all subscribed federations."""
        # Check if already banned in this federation
        existing_ban = await FederationBan.find_one(
            FederationBan.fed_id == federation.fed_id, FederationBan.user_id == user_id
        )
        if existing_ban:
            # Update reason if different
            if existing_ban.reason != reason:
                existing_ban.reason = reason
                await existing_ban.save()
            return existing_ban

        # Create new ban in this federation
        ban = FederationBan(
            fed_id=federation.fed_id,
            user_id=user_id,
            time=datetime.utcnow(),
            by=by_user,
            reason=reason,
        )
        await ban.insert()

        # Ban in all subscribed federations (but don't create DB entries - middleware handles enforcement)
        # This ensures the ban propagates through the subscription chain
        subscription_chain = await FederationService.get_subscription_chain(federation.fed_id)
        for sub_fed_id in subscription_chain:
            # Check if user is already banned in subscribed federation
            existing_sub_ban = await FederationBan.find_one(
                FederationBan.fed_id == sub_fed_id, FederationBan.user_id == user_id
            )
            if not existing_sub_ban:
                # Create ban in subscribed federation with origin_fed pointing to this federation
                sub_ban = FederationBan(
                    fed_id=sub_fed_id,
                    user_id=user_id,
                    time=datetime.utcnow(),
                    by=by_user,
                    reason=reason,
                    origin_fed=federation.fed_id,  # Mark this as originating from subscription
                )
                await sub_ban.insert()

        return ban

    @staticmethod
    async def unban_user(fed_id: str, user_id: int) -> tuple[bool, Optional[FederationBan]]:
        """Unban user from federation. Returns (success, ban_info_if_from_subscription)."""
        result = await FederationBan.find_one(FederationBan.fed_id == fed_id, FederationBan.user_id == user_id)
        if not result:
            return False, None

        # If this ban originated from a subscription, don't allow unbanning
        if hasattr(result, "origin_fed") and result.origin_fed:
            return False, result

        # Delete the ban
        await result.delete()

        # Also unban from federations that subscribe to this one
        # Find all federations that have this fed_id in their subscribed list
        subscribing_feds = await Federation.find(Federation.subscribed == fed_id).to_list()
        for sub_fed in subscribing_feds:
            # Only unban if the ban in the subscribing fed originated from this federation
            sub_ban = await FederationBan.find_one(
                FederationBan.fed_id == sub_fed.fed_id,
                FederationBan.user_id == user_id,
                FederationBan.origin_fed == fed_id,
            )
            if sub_ban:
                await sub_ban.delete()

        return True, None

    @staticmethod
    async def get_federation_bans(fed_id: str) -> List[FederationBan]:
        """Get all bans in a federation."""
        return await FederationBan.find(FederationBan.fed_id == fed_id).to_list()

    @staticmethod
    async def is_user_banned(fed_id: str, user_id: int) -> Optional[FederationBan]:
        """Check if user is banned in federation."""
        return await FederationBan.find_one(FederationBan.fed_id == fed_id, FederationBan.user_id == user_id)

    @staticmethod
    async def _can_user_create_federation(user_id: int) -> bool:
        """Check if user can create another federation."""
        # Owners can create unlimited federations
        if user_id == CONFIG.owner_id:
            return True

        # Count existing federations created by user
        count = await Federation.find(Federation.creator == user_id).count()
        return count < MAX_FEDERATIONS_PER_USER

    @staticmethod
    async def set_federation_log_channel(federation: Federation, chat_id: int) -> None:
        """Set the log channel for a federation."""
        federation.log_chat_id = chat_id
        await federation.save()

    @staticmethod
    async def remove_federation_log_channel(federation: Federation) -> None:
        """Remove the log channel for a federation."""
        federation.log_chat_id = None
        await federation.save()

    @staticmethod
    async def subscribe_to_federation(federation: Federation, target_fed_id: str) -> bool:
        """Subscribe federation to another federation. Returns True if successful."""
        # Check if target federation exists
        target_fed = await FederationService.get_federation_by_id(target_fed_id)
        if not target_fed:
            return False

        # Check if already subscribed
        if federation.subscribed and target_fed_id in federation.subscribed:
            return False

        # Prevent self-subscription
        if federation.fed_id == target_fed_id:
            return False

        # Add subscription
        if federation.subscribed is None:
            federation.subscribed = []
        federation.subscribed.append(target_fed_id)
        await federation.save()
        return True

    @staticmethod
    async def unsubscribe_from_federation(federation: Federation, target_fed_id: str) -> bool:
        """Unsubscribe federation from another federation. Returns True if successful."""
        if not federation.subscribed or target_fed_id not in federation.subscribed:
            return False

        federation.subscribed.remove(target_fed_id)
        await federation.save()
        return True

    @staticmethod
    async def get_subscription_chain(fed_id: str) -> List[str]:
        """Get all federations in the subscription chain (recursive)."""
        chain = []
        visited = set()

        async def _collect_subs(current_fed_id: str):
            if current_fed_id in visited:
                return  # Prevent cycles
            visited.add(current_fed_id)

            fed = await FederationService.get_federation_by_id(current_fed_id)
            if not fed or not fed.subscribed:
                return

            for sub_fed_id in fed.subscribed:
                if sub_fed_id not in chain:
                    chain.append(sub_fed_id)
                    await _collect_subs(sub_fed_id)

        await _collect_subs(fed_id)
        return chain

    @staticmethod
    async def is_user_banned_in_chain(fed_id: str, user_id: int) -> Optional[tuple[FederationBan, Federation]]:
        """Check if user is banned in federation or any subscribed federation."""
        # Check direct ban first
        direct_ban = await FederationService.is_user_banned(fed_id, user_id)
        if direct_ban:
            fed = await FederationService.get_federation_by_id(fed_id)
            if fed:
                return direct_ban, fed

        # Check subscription chain
        chain = await FederationService.get_subscription_chain(fed_id)
        for sub_fed_id in chain:
            ban = await FederationService.is_user_banned(sub_fed_id, user_id)
            if ban:
                fed = await FederationService.get_federation_by_id(sub_fed_id)
                if fed:
                    return ban, fed

        return None

    @staticmethod
    async def post_federation_log(federation: Federation, text: str, bot: Bot | None) -> None:
        """Post a log message to the federation's log channel."""
        if not federation.log_chat_id or not bot:
            return

        try:
            await bot.send_message(federation.log_chat_id, text)
        except (TelegramBadRequest, TelegramForbiddenError):
            # If we can't send to the log channel, silently ignore
            # Could potentially remove the log channel if it's invalid
            pass
