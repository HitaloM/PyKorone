import logging
import sys

import structlog

from sophie_bot import CONFIG

structlog.configure(
    cache_logger_on_first_use=True,
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
)
log = structlog.get_logger()

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.DEBUG if CONFIG.debug_mode else logging.INFO,
)
