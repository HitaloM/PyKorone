# Re-export from new location for backwards compatibility
# TODO: Update all imports to use sophie_bot.utils.handlers directly
from sophie_bot.utils.handlers import (
    SophieBaseHandler,
    SophieCallbackQueryHandler,
    SophieMessageCallbackQueryHandler,
    SophieMessageHandler,
)

__all__ = [
    "SophieBaseHandler",
    "SophieCallbackQueryHandler",
    "SophieMessageCallbackQueryHandler",
    "SophieMessageHandler",
]
