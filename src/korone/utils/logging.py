# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import logging
import sys
from dataclasses import dataclass
from typing import Any

import logfire
import structlog
from logfire import Logfire
from structlog.stdlib import BoundLogger
from structlog.types import Processor

LOG_LEVEL = logging.DEBUG if "--debug" in sys.argv else logging.INFO


@dataclass(slots=True)
class _LoggingState:
    logfire_instance: Logfire


_STATE = _LoggingState(logfire.configure(send_to_logfire=False))


def configure_logging(*, logfire_instance: Logfire | None = None) -> None:
    """Configure a lightweight structlog stack enriched with Logfire support.

    The setup wires a single root handler, uses a console-friendly renderer when running in a
    TTY, falls back to JSON otherwise, and keeps custom levels for noisy third-party libraries.

    Args:
        logfire_instance: Optional Logfire instance to route structlog events through. When
            omitted, falls back to the instance configured during module import.
    """
    if logfire_instance is not None:
        _STATE.logfire_instance = logfire_instance

    logging.basicConfig(level=LOG_LEVEL, format="%(message)s", stream=sys.stderr, force=True)

    for name, level in {"hydrogram": logging.INFO, "aiohttp": logging.WARNING}.items():
        third_party_logger = logging.getLogger(name)
        third_party_logger.setLevel(level)
        third_party_logger.propagate = False

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.format_exc_info,
        logfire.StructlogProcessor(logfire_instance=_STATE.logfire_instance),
    ]

    renderer: Processor
    if sys.stderr.isatty():
        renderer = structlog.dev.ConsoleRenderer(colors=True, sort_keys=False)
    else:
        renderer = structlog.processors.JSONRenderer(sort_keys=False)

    structlog.configure(
        processors=[*shared_processors, renderer],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None, **initial_values: Any) -> BoundLogger:
    """Return a configured structlog logger with optional contextual bindings.

    Args:
        name (str | None): Optional logger name, typically ``__name__`` of the caller.
        **initial_values (Any): Optional key-value pairs to bind immediately.

    Returns:
        BoundLogger: The configured logger augmented with any provided context.
    """

    log = structlog.get_logger(name) if name else structlog.get_logger()
    if initial_values:
        log = log.bind(**initial_values)
    return log


logger = get_logger("korone")
