from aiogram.utils.i18n import ConstI18nMiddleware
from ass_tg.middleware import ArgsMiddleware

from sophie_bot import CONFIG, dp
from sophie_bot.middlewares.beta import BetaMiddleware
from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.middlewares.legacy_save_chats import LegacySaveChats
from sophie_bot.middlewares.localization import LocalizationMiddleware
from sophie_bot.middlewares.logic import OrMiddleware
from sophie_bot.middlewares.save_chats import SaveChatsMiddleware
from sophie_bot.utils.i18n import I18nNew

i18n = I18nNew(path="locales", domain="bot", default_locale=CONFIG.default_locale)
localization_middleware = LocalizationMiddleware(i18n)
try_localization_middleware = OrMiddleware(localization_middleware, ConstI18nMiddleware("en_US", i18n))


def enable_middlewares():
    if CONFIG.debug_mode:
        from .debug import UpdateDebugMiddleware

        dp.update.middleware(UpdateDebugMiddleware())

    dp.update.outer_middleware(SaveChatsMiddleware())
    dp.message.outer_middleware(LegacySaveChats())

    dp.update.middleware(localization_middleware)
    dp.update.middleware(ConnectionsMiddleware())

    dp.message.middleware(ArgsMiddleware(i18n=i18n))

    if CONFIG.debug_mode:
        from .debug import DataDebugMiddleware, HandlerDebugMiddleware

        dp.update.middleware(DataDebugMiddleware())
        dp.update.middleware(HandlerDebugMiddleware())


def enable_proxy_middlewares():
    dp.update.middleware(BetaMiddleware())

    dp.message.middleware(ArgsMiddleware(i18n=i18n))
