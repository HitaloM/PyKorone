from __future__ import annotations

from sophie_bot.metrics.ai import (
    instrument_ai_operation,
    set_ai_metrics,
    track_ai_conversation,
    track_ai_request,
    track_ai_tool,
    track_ai_usage,
)
from sophie_bot.metrics.background import start_background_tasks, time_external
from sophie_bot.metrics.external import (
    create_service_tracker,
    instrument_external_service,
    instrument_mongo,
    instrument_openai,
    instrument_redis,
    instrument_telegram_api,
    set_metrics,
    time_external_service,
    time_mongo_operation,
    time_openai_operation,
    time_redis_operation,
    time_telegram_api_operation,
)
from sophie_bot.metrics.middleware import MetricsMiddleware
from sophie_bot.metrics.prom import (
    SophieMetrics,
    aiohttp_handler,
    create_registry,
    make_metrics,
    push_to_gateway,
    start_http_exporter,
)

__all__ = [
    "SophieMetrics",
    "MetricsMiddleware",
    "create_registry",
    "make_metrics",
    "start_http_exporter",
    "aiohttp_handler",
    "push_to_gateway",
    "start_background_tasks",
    "time_external",
    # External service instrumentation
    "set_metrics",
    "time_external_service",
    "instrument_external_service",
    "instrument_mongo",
    "instrument_redis",
    "instrument_openai",
    "instrument_telegram_api",
    "time_mongo_operation",
    "time_redis_operation",
    "time_openai_operation",
    "time_telegram_api_operation",
    "create_service_tracker",
    # AI metrics instrumentation
    "set_ai_metrics",
    "track_ai_request",
    "track_ai_tool",
    "track_ai_usage",
    "track_ai_conversation",
    "instrument_ai_operation",
]
