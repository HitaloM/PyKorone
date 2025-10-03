# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict, Processor

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "korone.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

LOG_LEVEL = logging.DEBUG if "--debug" in sys.argv else logging.INFO


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

    This function sets up a logging configuration that supports both colored console output and
    JSON-formatted file output. It defines custom formatters, handlers, and logger settings for
    the root logger and specific third-party libraries. The configuration includes log rotation
    for file logs and enhanced log context processing using structlog processors.

    Raises:
        ValueError: If the logging configuration is invalid.
    """
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    ]

    logging_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    extract_context_info,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(sort_keys=False),
                ],
                "foreign_pre_chain": shared_processors,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    extract_context_info,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True, sort_keys=False),
                ],
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "console": {
                "level": LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "file": {
                "level": LOG_LEVEL,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "plain",
                "filename": LOG_FILE,
                "maxBytes": MAX_LOG_SIZE,
                "backupCount": BACKUP_COUNT,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": LOG_LEVEL,
                "propagate": True,
            },
            # Third-party library logging levels
            "hydrogram": {
                "level": logging.INFO,
                "handlers": ["console", "file"],
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
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


configure_logging()

logger = structlog.get_logger()
