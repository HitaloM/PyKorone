import uvloop
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from ass_tg.middleware import ArgsMiddleware

from . import bot, dp
from .config import CONFIG
from .db.repositories.chat import ChatRepository
from .db.utils import close_db, init_db
from .logger import get_logger, setup_logging
from .middlewares import localization_middleware
from .middlewares.chat_context import ChatContextMiddleware
from .middlewares.disabling import DisablingMiddleware
from .middlewares.save_chats import SaveChatsMiddleware
from .modules import load_modules
from .utils.aiohttp_session import HTTPClient
from .utils.i18n import i18n

uvloop.install()

logger = get_logger(__name__)

WEBHOOK_URL = f"{CONFIG.webhook_domain}{CONFIG.webhook_path}"


async def ensure_bot_in_db() -> None:
    bot_user = await bot.get_me()
    await ChatRepository.upsert_user(bot_user)
    await logger.ainfo("Bot user ensured in DB", bot_id=bot_user.id, username=bot_user.username)


async def on_startup() -> None:
    await logger.ainfo("Starting up the bot via Webhook...")

    await init_db()
    await ensure_bot_in_db()
    await load_modules(dp, ["*"], CONFIG.modules_not_load)

    dp.update.middleware(localization_middleware)
    dp.message.middleware(ArgsMiddleware(i18n=i18n))
    dp.update.outer_middleware(SaveChatsMiddleware())
    dp.update.middleware(ChatContextMiddleware())
    dp.message.middleware(DisablingMiddleware())

    await bot.set_webhook(url=WEBHOOK_URL, allowed_updates=dp.resolve_used_update_types(), drop_pending_updates=True)
    await logger.ainfo(f"Webhook set to: {WEBHOOK_URL}")


async def on_shutdown() -> None:
    await logger.ainfo("Shutting down the bot...")
    await bot.delete_webhook()
    await close_db()
    await HTTPClient.close()
    await bot.session.close()
    await dp.storage.close()


def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=CONFIG.webhook_path)

    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=CONFIG.web_server_port)


if __name__ == "__main__":
    setup_logging()
    main()
