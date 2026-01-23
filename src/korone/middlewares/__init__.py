from aiogram.utils.i18n import ConstI18nMiddleware

from korone.middlewares.localization import LocalizationMiddleware
from korone.middlewares.logic import OrMiddleware
from korone.utils.i18n import i18n

localization_middleware = LocalizationMiddleware(i18n)
try_localization_middleware = OrMiddleware(localization_middleware, ConstI18nMiddleware("en_US", i18n))
