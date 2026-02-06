from __future__ import annotations

from aiogram import flags
from stfu_tg import Code, Doc, Template

from korone import aredis
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Clear Redis cache for the bot."))
class RedisClearHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple:
        return (CMDFilter("flushredis"), IsOP(is_op=True))

    async def handle(self) -> None:
        before = await aredis.dbsize()
        await aredis.flushdb()
        after = await aredis.dbsize()
        removed = max(before - after, 0)

        message = Doc(Template(l_("Redis cleared. {removed} keys removed."), removed=Code(removed)))
        await self.event.reply(str(message))
