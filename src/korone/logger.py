import logging
import sys
from typing import TYPE_CHECKING

import structlog
from structlog.dev import plain_traceback

if TYPE_CHECKING:
    from structlog.typing import Processor


def setup_logging(level: int = logging.INFO) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.processors.CallsiteParameterAdder(
                    parameters=[
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ]
                ),
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True, exception_formatter=plain_traceback),
            ],
            foreign_pre_chain=[*shared_processors, structlog.stdlib.ExtraAdder()],
        )
    )

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        *shared_processors,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
