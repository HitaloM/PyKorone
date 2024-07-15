import logging
import sys

import structlog

from sophie_bot import CONFIG

level = logging.DEBUG if CONFIG.debug_mode else logging.INFO

structlog.configure(
    cache_logger_on_first_use=True,
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(level),
)
log = structlog.get_logger()

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=level,
)
