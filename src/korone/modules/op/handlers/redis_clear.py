from aiogram import flags
from aiogram.filters import Command

from korone import aredis
from korone.filters.user_status import IsOP
from korone.ui import Code, column, template
from korone.utils.handlers import KoroneMessageHandler


@flags.help(description="Clear the bot Redis cache.")
class RedisClearHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple:
        return (Command("flushredis"), IsOP(is_op=True))

    async def handle(self) -> None:
        async with aredis.pipeline() as pipeline:
            pipeline.dbsize()
            pipeline.flushdb()
            pipeline.dbsize()
            before, _, after = await pipeline.execute()
        removed = max(before - after, 0)

        message = column(template("Redis cleared. {removed} keys removed.", removed=Code(removed)))
        await self.answer(message)
