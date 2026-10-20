from korone.config import CONFIG
from korone.logger import get_logger
from korone.modules.error.utils.capture import capture_sentry
from korone.utils.i18n import gettext as _

from .errors import (
    GSMArenaAccessError,
    GSMArenaError,
    GSMArenaParseError,
    GSMArenaRequestError,
    GSMArenaUnavailableError,
)

logger = get_logger(__name__)


async def report_failure(error: GSMArenaError, *, operation: str) -> str:
    sentry_event_id = capture_sentry(error) if isinstance(error, GSMArenaParseError) else None
    await logger.awarning(
        "[GSM Arena] Lookup failed",
        operation=operation,
        via_proxy=CONFIG.cors_bypass_url is not None,
        error_type=type(error).__name__,
        cause_type=type(error.__cause__).__name__ if error.__cause__ is not None else None,
        status_code=error.status_code if isinstance(error, GSMArenaRequestError) else None,
        sentry_event_id=sentry_event_id,
        exc_info=(type(error), error, error.__traceback__) if isinstance(error, GSMArenaParseError) else None,
    )
    if isinstance(error, GSMArenaAccessError):
        if error.status_code == 429:
            return _("GSMArena is receiving too many requests. Please try again later.")
        return _("GSMArena is restricting automated access. Please try searching on its website.")
    if isinstance(error, GSMArenaUnavailableError):
        return _("GSMArena is temporarily unavailable. Please try again later.")
    if isinstance(error, GSMArenaParseError):
        return _("GSMArena returned an unexpected page. Device data could not be read. Please try again later.")
    return _("Could not retrieve data from GSMArena. Please try again later.")
