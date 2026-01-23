import argparse
import logging

import anyio
from ass_tg.middleware import ArgsMiddleware

from . import bot, dp
from .config import CONFIG
from .db.init import init_db
from .db.models.chat import ChatModel
from .db.session import dispose_engine
from .logging import get_logger, setup_logging
from .middlewares import localization_middleware
from .middlewares.chat_context import ChatContextMiddleware
from .middlewares.disabling import DisablingMiddleware
from .middlewares.save_chats import SaveChatsMiddleware
from .modules import load_modules
from .utils.i18n import i18n

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Korone Bot")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


async def ensure_bot_in_db() -> None:
    bot_user = await bot.get_me()
    await ChatModel.upsert_user(bot_user)
    await logger.ainfo("Bot user ensured in DB", bot_id=bot_user.id, username=bot_user.username)


async def main() -> None:
    await logger.ainfo("Starting the bot...")

    try:
        await init_db()
        await ensure_bot_in_db()
        await load_modules(dp, ["*"], CONFIG.modules_not_load)

        dp.update.middleware(localization_middleware)
        dp.message.middleware(ArgsMiddleware(i18n=i18n))
        dp.update.outer_middleware(SaveChatsMiddleware())
        dp.update.middleware(ChatContextMiddleware())
        dp.message.middleware(DisablingMiddleware())

        allowed_updates = dp.resolve_used_update_types()
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await dispose_engine()


if __name__ == "__main__":
    args = parse_args()
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    anyio.run(main, backend="asyncio", backend_options={"use_uvloop": True})
