import ssl
from importlib import import_module

from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    ip_filter_middleware,
    setup_application,
)
from aiogram.webhook.security import IPFilter
from aiohttp.web import run_app
from aiohttp.web_app import Application

from sophie_bot import bot, dp
from sophie_bot.config import CONFIG
from sophie_bot.middlewares import enable_middlewares, enable_proxy_middlewares
from sophie_bot.modules import load_modules
from sophie_bot.services.apscheduller import start_apscheduller
from sophie_bot.services.db import init_db, test_db
from sophie_bot.services.telethon import start_telethon
from sophie_bot.utils.logger import log

if CONFIG.proxy_enabled:
    log.warn(
        "Proxy mode enabled!",
        stable_instance_url=CONFIG.stable_instance_url,
        beta_instance_url=CONFIG.beta_instance_url,
    )

    enable_proxy_middlewares()
    load_modules(dp, ["error", "beta"], [])
else:
    enable_middlewares()
    load_modules(dp, ["*"], CONFIG.modules_not_load)

# Import misc stuff
if not CONFIG.debug_mode:
    import_module("sophie_bot.utils.sentry")


@dp.startup()
async def start():
    await init_db()
    await test_db()

    await start_telethon()
    await start_apscheduller()


if not CONFIG.webhooks_enable:
    dp.run_polling(
        bot,
        allowed_updates=[
            "message",
            "edited_message",
            # 'channel_post',
            # 'edited_channel_post',
            "inline_query",
            # 'chosen_inline_result',
            "callback_query",
            # 'shipping_query',
            # 'pre_checkout_query',
            # 'poll',
            # 'poll_answer',
            "my_chat_member",
            "chat_member",
            "chat_join_request",
        ],
    )
else:
    app = Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        handle_in_background=CONFIG.webhooks_handle_in_background,
        secret_token=CONFIG.webhooks_secret_token,
    ).register(app, path=CONFIG.webhooks_path)

    if CONFIG.webhooks_filter_ips:
        # TODO: Long start
        log.info("Filtering IP addresses", ips=CONFIG.webhooks_allowed_networks)
        app.middlewares.append(ip_filter_middleware(IPFilter(CONFIG.allowed_networks)))

    setup_application(app, dp, bot=bot)

    if CONFIG.webhooks_https_certificate:
        log.info("Using HTTPs!")

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_cert_chain(CONFIG.webhooks_https_certificate, CONFIG.webhooks_https_certificate_key)
    else:
        ssl_context = None
        log.warn("Using HTTP (use it only for reverse-proxy or development)!")

    run_app(
        app,
        host=CONFIG.webhooks_listen,
        port=CONFIG.webhooks_port,
        ssl_context=ssl_context,
    )
