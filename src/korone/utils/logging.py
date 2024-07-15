# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import sys

import picologging as logging
import structlog

level = logging.DEBUG if "--debug" in sys.argv else logging.INFO

structlog.configure(
    cache_logger_on_first_use=True,
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="%d-%m-%Y %H:%M.%S", utc=False),
        structlog.dev.ConsoleRenderer(),
    ],
)

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=level,
)

logger = structlog.wrap_logger(logging.getLogger("korone"))
