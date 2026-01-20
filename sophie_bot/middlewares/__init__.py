from aiogram.utils.i18n import ConstI18nMiddleware
from ass_tg.middleware import ArgsMiddleware

from sophie_bot.config import CONFIG
from sophie_bot.middlewares.beta import BetaMiddleware
from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.middlewares.disabling import DisablingMiddleware
from sophie_bot.middlewares.localization import LocalizationMiddleware
from sophie_bot.middlewares.logic import OrMiddleware
from sophie_bot.middlewares.memory_debug import TracemallocMiddleware
from sophie_bot.middlewares.save_chats import SaveChatsMiddleware
from sophie_bot.services.bot import dp
from sophie_bot.services.i18n import i18n
from sophie_bot.utils.logger import log

# Global metrics instance - will be set during initialization
_metrics_middleware = None

localization_middleware = LocalizationMiddleware(i18n)
try_localization_middleware = OrMiddleware(localization_middleware, ConstI18nMiddleware("en_US", i18n))


def set_metrics_middleware(middleware) -> None:
    """Set the metrics middleware instance"""
    global _metrics_middleware
    _metrics_middleware = middleware
    log.info("Metrics middleware set")


def enable_middlewares():
    if CONFIG.debug_mode in ("normal", "high"):
        from .debug import EventSeparatorMiddleware

        dp.update.outer_middleware(EventSeparatorMiddleware())

    if CONFIG.debug_mode == "high":
        from .debug import UpdateDebugMiddleware

        dp.update.middleware(UpdateDebugMiddleware())

    dp.update.middleware(localization_middleware)

    # Register metrics middleware if enabled
    if CONFIG.metrics_enable and _metrics_middleware:
        dp.update.middleware(_metrics_middleware)
        log.info("Metrics middleware registered")

    if CONFIG.proxy_enable:
        log.info("Enabled Proxy!")
        dp.update.middleware(BetaMiddleware())

    dp.message.middleware(ArgsMiddleware(i18n=i18n))

    dp.update.outer_middleware(SaveChatsMiddleware())

    dp.update.middleware(ConnectionsMiddleware())
    dp.message.middleware(DisablingMiddleware())

    if CONFIG.debug_mode == "high":
        from .debug import DataDebugMiddleware, HandlerDebugMiddleware

        dp.update.middleware(DataDebugMiddleware())
        dp.update.middleware(HandlerDebugMiddleware())

    if CONFIG.memory_debug:
        dp.update.middleware(TracemallocMiddleware())
