import ssl
from typing import Optional

from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    ip_filter_middleware,
    setup_application,
)
from aiogram.webhook.security import IPFilter
from aiohttp.web import run_app
from aiohttp.web_app import Application

from sophie_bot.config import CONFIG
from sophie_bot.middlewares import enable_middlewares, set_metrics_middleware
from sophie_bot.services.bot import bot, dp
from sophie_bot.startup import start_init
from sophie_bot.utils.logger import log


@dp.startup()
async def bot_start():
    await start_init(dp)

    # Initialize metrics system if enabled
    if CONFIG.metrics_enable:
        await _init_metrics()

    enable_middlewares()


async def _init_metrics():
    """Initialize the metrics system"""
    try:
        from sophie_bot.metrics import (
            MetricsMiddleware,
            create_registry,
            make_metrics,
            set_metrics,
            start_background_tasks,
            start_http_exporter,
        )

        # Create registry and metrics
        registry = create_registry(CONFIG)
        metrics = make_metrics(registry, CONFIG)

        # Start HTTP exporter (separate port)
        start_http_exporter(registry=registry, host=CONFIG.metrics_listen_host, port=CONFIG.metrics_listen_port)

        # Start background tasks
        await start_background_tasks(metrics, CONFIG)

        # Initialize external service metrics
        set_metrics(metrics)

        # Initialize AI metrics
        from sophie_bot.metrics import set_ai_metrics

        set_ai_metrics(metrics)

        # Create and set middleware
        metrics_middleware = MetricsMiddleware(metrics, CONFIG)
        set_metrics_middleware(metrics_middleware)

        log.info("Metrics system initialized successfully")

    except Exception as e:
        log.error("Failed to initialize metrics system", error=str(e))
        if CONFIG.debug_mode != "off":
            raise


def _add_metrics_to_webhook(app: Application) -> None:
    """Add metrics endpoint to webhook server"""
    try:
        from sophie_bot.metrics import aiohttp_handler, create_registry, make_metrics

        # Create registry and metrics for webhook
        registry = create_registry(CONFIG)
        make_metrics(registry, CONFIG)

        # Add metrics route
        metrics_handler = aiohttp_handler(registry)
        app.router.add_get(CONFIG.metrics_path, metrics_handler)

        log.info("Added metrics endpoint to webhook server", path=CONFIG.metrics_path)

    except Exception as e:
        log.error("Failed to add metrics endpoint to webhook", error=str(e))


def start_bot_mode() -> None:
    if CONFIG.dev_reload:
        from sophie_bot.utils.dev_runner import run_with_reload

        run_with_reload("bot")
        return

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
                # 'pre_chlegacy_moduleseckout_query',
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
            app.middlewares.append(ip_filter_middleware(IPFilter(CONFIG.webhooks_allowed_networks)))  # type: ignore

        setup_application(app, dp, bot=bot)

        # Add metrics endpoint to webhook server if enabled
        if CONFIG.metrics_enable and CONFIG.metrics_path_on_webhook:
            _add_metrics_to_webhook(app)

        ssl_context: Optional[ssl.SSLContext]
        if CONFIG.webhooks_https_certificate:
            log.info("Using HTTPs!")

            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.load_cert_chain(CONFIG.webhooks_https_certificate, CONFIG.webhooks_https_certificate_key)
        else:
            ssl_context = None
            log.warn("Using HTTP (use it only for reverse-proxy or development)!")

        run_app(app, host=CONFIG.webhooks_listen, port=CONFIG.webhooks_port, ssl_context=ssl_context)
