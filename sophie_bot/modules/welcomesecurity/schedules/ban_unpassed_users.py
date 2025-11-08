from datetime import datetime, timedelta, timezone

from sophie_bot.config import CONFIG
from sophie_bot.db.models.ws_user import WSUserModel
from sophie_bot.modules.legacy_modules.utils.restrictions import ban_user
from sophie_bot.services.bot import bot
from sophie_bot.utils.logger import log


class BanUnpassedUsers:
    async def process_user(self, ws_user: WSUserModel):
        await ws_user.fetch_all_links()

        user = ws_user.user
        group = ws_user.group
        log.debug("ban_unpassed_users: processing user", user=user.id, group=group.id)

        # Check if ban_timeout hours have passed
        if datetime.now(timezone.utc) - ws_user.added_at < timedelta(hours=CONFIG.welcomesecurity_ban_timeout):
            return

        # Check if entry is older than 36 hours
        is_old_entry = datetime.now(timezone.utc) - ws_user.added_at > timedelta(hours=36)

        if not ws_user.passed and not is_old_entry:
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
