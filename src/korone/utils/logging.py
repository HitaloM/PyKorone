# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import logging
import logging.config
import sys
from typing import Any

import logfire
import structlog
from structlog.stdlib import BoundLogger
from structlog.types import EventDict, Processor

LOG_LEVEL = logging.DEBUG if "--debug" in sys.argv else logging.INFO

logfire.configure(send_to_logfire=False)


def extract_context_info(_, __, event_dict: EventDict) -> EventDict:
    """
    Extracts contextual information from a log event dictionary and enriches it with thread,
    process, file, and line number details.

    Args:
        _ (Any): Unused positional argument, typically required by the processor interface.
        __ (Any): Unused positional argument, typically required by the processor interface.
        event_dict (EventDict): The event dictionary containing log record information.

    Returns:
        EventDict: The updated event dictionary with additional context fields:
            - "thread_name": Name of the thread where the log was emitted.
            - "process_name": Name of the process where the log was emitted.
            - "file": Pathname of the source file (if available).
            - "line": Line number in the source file (if available).
    """
    if "_record" in event_dict:
        record = event_dict["_record"]
        event_dict["thread_name"] = record.threadName
        event_dict["process_name"] = record.processName

        if hasattr(record, "pathname") and hasattr(record, "lineno"):
            event_dict["file"] = record.pathname
            event_dict["line"] = record.lineno

    return event_dict


def configure_logging() -> None:
    """
    Configures logging for the application using structlog and the standard logging module.

    This function sets up a logging configuration that supports colored console output paired with
    structlog processors and Logfire integration. It defines custom formatters, handlers, and
    logger settings for the root logger and specific third-party libraries.

    Raises:
        ValueError: If the logging configuration is invalid.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]

    formatter_processors: dict[str, list[Processor]] = {
        "console": [
            extract_context_info,
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True, sort_keys=False),
        ],
        "json": [
            extract_context_info,
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(sort_keys=False),
        ],
    }

    formatter_key = "console" if sys.stderr.isatty() else "json"

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            name: {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": processors,
                "foreign_pre_chain": shared_processors,
            }
            for name, processors in formatter_processors.items()
        },
        "handlers": {
            "console": {
                "level": LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": formatter_key,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": LOG_LEVEL,
                "propagate": True,
            },
            # Third-party library logging levels
            "hydrogram": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
            "aiohttp": {
                "level": logging.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            *shared_processors,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            logfire.StructlogProcessor(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
        cache_logger_on_first_use=True,
    )


configure_logging()


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
