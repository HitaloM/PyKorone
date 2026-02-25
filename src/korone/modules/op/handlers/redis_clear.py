from __future__ import annotations

from aiogram import flags
from aiogram.filters import Command
from stfu_tg import Code, Doc, Template

from korone import aredis
from korone.filters.user_status import IsOP
from korone.utils.handlers import KoroneMessageHandler


@flags.help(description="Clear Redis cache for the bot.")
class RedisClearHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple:
        return (Command("flushredis"), IsOP(is_op=True))

    async def handle(self) -> None:
        before = await aredis.dbsize()
        await aredis.flushdb()
        after = await aredis.dbsize()
        removed = max(before - after, 0)

        message = Doc(Template("Redis cleared. {removed} keys removed.", removed=Code(removed)))
        await self.event.reply(str(message))
