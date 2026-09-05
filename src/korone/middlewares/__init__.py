from korone.middlewares.localization import FallbackLocalizationMiddleware, LocalizationMiddleware
from korone.middlewares.log_context import UpdateLogContextMiddleware
from korone.utils.i18n import i18n

localization_middleware = LocalizationMiddleware(i18n)
fallback_localization_middleware = FallbackLocalizationMiddleware(i18n)

__all__ = ("UpdateLogContextMiddleware", "fallback_localization_middleware", "localization_middleware")
