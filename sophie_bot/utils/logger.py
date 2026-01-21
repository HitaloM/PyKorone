import logging.config
import os

import structlog
from aiogram.loggers import event
from structlog.typing import EventDict

from sophie_bot.config import CONFIG

timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")


def silence_processor(logger: logging.Logger, method_name: str, event_dict: EventDict):
    if event_dict.get("logger", None) == "aiogram.event":
        event_dict["level"] = "debug"

    return event_dict


def mongo_prefix_processor(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add 'mongo: ' prefix to pymongo log messages and make them gray."""
    logger_name = event_dict.get("logger", "")
    if logger_name and logger_name.startswith("pymongo."):
        event = event_dict.get("event", "")
        if event and not event.startswith("mongo: "):
            # Use ANSI escape codes for gray (dim) text
            gray = "\033[90m"
            reset = "\033[0m"
            event_dict["event"] = f"mongo: {gray}{event}{reset}"
    return event_dict


def security_color_processor(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    logger_name = event_dict.get("logger", "")
    if logger_name == "security":
        event = event_dict.get("event", "")
        if event:
            orange = "\033[38;5;208m"
            reset = "\033[0m"
            event_dict["event"] = f"{orange}{event}{reset}"
    return event_dict


pre_chain = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    timestamper,
    silence_processor,
    mongo_prefix_processor,
]

# Debug levels: off = INFO, normal/high = DEBUG
level = logging.DEBUG if CONFIG.debug_mode in ("normal", "high") else logging.INFO
# Mongo log level: only DEBUG in "high" mode, otherwise WARNING
mongo_level = logging.DEBUG if CONFIG.debug_mode == "high" else logging.WARNING


def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.
    """
    record = event_dict["_record"]
    event_dict["thread_name"] = record.threadName
    event_dict["process_name"] = record.processName
    return event_dict


os.makedirs(os.path.dirname(CONFIG.security_log_file), exist_ok=True)


logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(sort_keys=False),
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    security_color_processor,
                    structlog.dev.ConsoleRenderer(colors=True, sort_keys=False),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": {
            "default": {
                "level": level,
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
            "security_file": {
                "level": level,
                "class": "logging.handlers.WatchedFileHandler",
                "filename": CONFIG.security_log_file,
                "formatter": "plain",
            },
            # "file": {
            #     "level": level,
            #     "class": "logging.handlers.WatchedFileHandler",
            #     "filename": "test.log",
            #     "formatter": "plain",
            # },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": level,
                "propagate": True,
            },
            "security": {
                "handlers": ["security_file", "default"],
                "level": level,
                "propagate": False,
            },
            "pymongo.topology": {
                "level": mongo_level,
                "propagate": True,
            },
            "pymongo.serverSelection": {
                "level": mongo_level,
                "propagate": True,
            },
            "pymongo.connection": {
                "level": mongo_level,
                "propagate": True,
            },
            "pymongo.command": {
                "level": mongo_level,
                "propagate": True,
            },
            "watchfiles.main": {
                "level": logging.WARNING,
                "propagate": True,
            },
        },
    }
)
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        # structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

event.setLevel(logging.DEBUG)
log = structlog.get_logger()
security_log = structlog.get_logger("security")
