# ... existing code ...
from datetime import datetime, timedelta, timezone
from sophie_bot.config import CONFIG
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.ws_user import WSUserModel
from sophie_bot.modules.legacy_modules.utils.restrictions import ban_user
from sophie_bot.services.bot import bot
from sophie_bot.utils.logger import log


class BanUnpassedUsers:
    @staticmethod
    async def process_user(ws_user: WSUserModel):
        # Early return if already passed
        if ws_user.passed:
            log.debug("ban_unpassed_users: skipping ws_user, already passed", ws_user_id=str(ws_user.id))
            return

        # Ensure we have a valid ID and added_at timestamp
        if not ws_user.id:
            log.error("ban_unpassed_users: skipping ws_user due to missing id", ws_user_id=str(ws_user.id))
            return

        # Validate linked references exist
        try:
            user = await ChatModel.get_by_iid(ws_user.user.ref.id)
            group = await ChatModel.get_by_iid(ws_user.group.ref.id)
        except (AttributeError, Exception) as e:
            log.warning(
                "ban_unpassed_users: skipping ws_user due to invalid link references",
                ws_user_id=str(ws_user.id),
                error=str(e),
            )
            await ws_user.delete()
            return

        if user is None or group is None:
            log.warning(
                "ban_unpassed_users: skipping ws_user due to missing linked user/group",
                ws_user_id=str(ws_user.id),
            )
            await ws_user.delete()
            return
        log.debug("ban_unpassed_users: processing user", user=user.id, group=group.id)

        added_at = ws_user.added_at or ws_user.id.generation_time
        # Ensure added_at is timezone-aware
        if added_at.tzinfo is None:
            added_at = added_at.replace(tzinfo=timezone.utc)
        is_old_entry = datetime.now(timezone.utc) - added_at > timedelta(hours=CONFIG.welcomesecurity_ban_timeout)
        if not is_old_entry:
            log.debug("ban_unpassed_users: skipping ws_user, too young", ws_user_id=str(ws_user.id))
            return
        # Check for legacy entries - delete them if old
        if not ws_user.added_at:
            log.warning("ban_unpassed_users: skipping ws_user due to missing added_at", ws_user_id=str(ws_user.id))
            await ws_user.delete()
            return

        # Process unpassed user (no need to check ws_user.passed again)
        if ws_user.is_join_request:
            # Decline the join request
            try:
                await bot.decline_chat_join_request(chat_id=group.chat_id, user_id=user.chat_id)
                log.info("ban_unpassed_users: declined join request", user=user.chat_id, group=group.chat_id)
            except Exception as e:
                log.error(
                    "ban_unpassed_users: failed to decline join request",
                    user=user.chat_id,
                    group=group.chat_id,
                    error=str(e),
                )
        else:
            # Ban the user
            try:
                await ban_user(chat_id=group.chat_id, user_id=user.chat_id)
                log.info("ban_unpassed_users: banned user", user=user.chat_id, group=group.chat_id)
            except Exception as e:
                log.error(
                    "ban_unpassed_users: failed to ban user", user=user.chat_id, group=group.chat_id, error=str(e)
                )

        # Remove from database
        await ws_user.delete()

    async def handle(self):
        log.debug("ban_unpassed_users: starting")

        async for ws_user in WSUserModel.find({"passed": False}):
            await self.process_user(ws_user)

        log.debug("ban_unpassed_users: finished")
