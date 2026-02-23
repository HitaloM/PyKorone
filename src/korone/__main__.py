import asyncio
import logging

import sentry_sdk
import uvloop
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from ass_tg.middleware import ArgsMiddleware
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from korone.modules.error.utils.ignored import IGNORED_EXCEPTIONS

from . import bot, dp
from .config import CONFIG
from .db.repositories.chat import ChatRepository
from .db.utils import close_db, init_db, migrate_db_if_needed
from .logger import get_logger, setup_logging
from .middlewares import localization_middleware
from .middlewares.admin_cache import AdminCacheMiddleware
from .middlewares.chat_context import ChatContextMiddleware
from .middlewares.disabling import DisablingMiddleware
from .middlewares.save_chats import SaveChatsMiddleware
from .modules import load_modules
from .utils.aiohttp_session import HTTPClient
from .utils.i18n import i18n

logger = get_logger(__name__)


async def ensure_bot_in_db() -> None:
    bot_user = await bot.get_me()
    await ChatRepository.upsert_user(bot_user)
    await logger.ainfo("Bot user ensured in DB", bot_id=bot_user.id, username=bot_user.username)


def configure_dispatcher() -> None:
    dp.update.middleware(localization_middleware)
    dp.message.middleware(DisablingMiddleware())
    dp.message.middleware(ArgsMiddleware(i18n=i18n))
    dp.update.outer_middleware(SaveChatsMiddleware())
    dp.update.middleware(AdminCacheMiddleware())
    dp.update.middleware(ChatContextMiddleware())


def get_allowed_updates() -> list[str]:
    return dp.resolve_used_update_types()


def get_webhook_url() -> str:
    return f"{CONFIG.webhook_domain}{CONFIG.webhook_path}"


async def bootstrap() -> None:
    await logger.ainfo("Starting up the bot...")

    if CONFIG.sentry_url:
        await logger.ainfo("Starting sentry.io integration...")

        sentry_sdk.init(
            str(CONFIG.sentry_url),
            integrations=[RedisIntegration(), AioHttpIntegration(), SqlalchemyIntegration()],
            ignore_errors=IGNORED_EXCEPTIONS,
        )

    await init_db()
    await migrate_db_if_needed()
    await ensure_bot_in_db()
    await load_modules(dp, CONFIG.modules_load, CONFIG.modules_not_load)


async def shutdown() -> None:
    await logger.ainfo("Shutting down the bot...")
    await close_db()
    await HTTPClient.close()
    await bot.delete_webhook()
    await bot.session.close()
    await dp.storage.close()


async def run_polling() -> None:
    try:
        await logger.awarning("No webhook domain configured, running in long polling mode")
        await bootstrap()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=get_allowed_updates(), close_bot_session=False)
    finally:
        await shutdown()


def create_webhook_app() -> web.Application:
    app = web.Application()

    async def on_startup(_: web.Application) -> None:
        await bootstrap()
        webhook_url = get_webhook_url()
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=get_allowed_updates(),
            drop_pending_updates=True,
            secret_token=CONFIG.webhook_secret,
        )
        await logger.ainfo("Webhook set", webhook_url=webhook_url)

    async def on_shutdown(_: web.Application) -> None:
        await shutdown()

    app.on_startup.append(on_startup)
    setup_application(app, dp, bot=bot)
    app.on_shutdown.append(on_shutdown)

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=CONFIG.webhook_secret)
    webhook_handler.register(app, path=CONFIG.webhook_path)

    return app


def main() -> None:
    configure_dispatcher()

    if CONFIG.webhook_domain:
        app = create_webhook_app()
        web.run_app(app, host="0.0.0.0", port=CONFIG.web_server_port)
        return

    asyncio.run(run_polling())


if __name__ == "__main__":
    setup_logging(level=logging.DEBUG if CONFIG.debug_mode else logging.INFO)
    uvloop.install()
    main()
