from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any

from aiohttp import web
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    start_http_server,
)

from sophie_bot.constants import METRICS_HISTOGRAM_BUCKETS
from sophie_bot.utils.logger import log


@dataclass
class SophieMetrics:
    """Container for all Sophie Bot metrics"""

    # Counters
    updates_total: Counter
    messages_total: Counter
    handler_errors_total: Counter
    external_errors_total: Counter

    # Gauges
    inflight_handlers: Gauge
    event_loop_lag_seconds: Gauge

    # Histograms
    handler_duration_seconds: Histogram
    external_request_duration_seconds: Histogram

    # Info
    build_info: Info

    # AI-specific metrics
    # Counters
    ai_requests_total: Counter
    ai_tokens_total: Counter
    ai_tool_calls_total: Counter
    ai_errors_total: Counter

    # Gauges
    ai_active_conversations: Gauge

    # Histograms
    ai_request_duration_seconds: Histogram
    ai_tool_duration_seconds: Histogram


def create_registry(config: Any) -> CollectorRegistry:
    """Create Prometheus registry with constant labels"""
    registry = CollectorRegistry()

    # Add default collectors if enabled
    if config.metrics_enable_default_collectors:
        from prometheus_client import (
            PROCESS_COLLECTOR,
            PLATFORM_COLLECTOR,
            GC_COLLECTOR,
        )

        registry.register(PROCESS_COLLECTOR)
        registry.register(PLATFORM_COLLECTOR)
        registry.register(GC_COLLECTOR)

    return registry


def make_metrics(registry: CollectorRegistry, config: Any) -> SophieMetrics:
    """Create all Sophie Bot metrics and register them with the registry"""

    # Create metrics
    updates_total = Counter(
        "sophie_updates_total",
        "Total number of Telegram updates processed",
        ["update_type", "chat_type", "transport"],
        registry=registry,
    )

    messages_total = Counter(
        "sophie_messages_total", "Total number of messages processed", ["message_kind"], registry=registry
    )

    handler_errors_total = Counter(
        "sophie_handler_errors_total", "Total number of handler errors", ["handler", "exception"], registry=registry
    )

    external_errors_total = Counter(
        "sophie_external_errors_total",
        "Total number of external service errors",
        ["service", "exception"],
        registry=registry,
    )

    inflight_handlers = Gauge(
        "sophie_inflight_handlers", "Number of handlers currently being processed", registry=registry
    )

    event_loop_lag_seconds = Gauge("sophie_event_loop_lag_seconds", "Event loop lag in seconds", registry=registry)

    # Create histogram buckets
    buckets = METRICS_HISTOGRAM_BUCKETS

    handler_duration_seconds = Histogram(
        "sophie_handler_duration_seconds",
        "Handler execution duration in seconds",
        ["handler"],
        buckets=buckets,
        registry=registry,
    )

    external_request_duration_seconds = Histogram(
        "sophie_external_request_duration_seconds",
        "External service request duration in seconds",
        ["service"],
        buckets=buckets,
        registry=registry,
    )

    build_info = Info("sophie_build_info", "Build information", registry=registry)

    # AI-specific metrics
    ai_requests_total = Counter(
        "sophie_ai_requests_total",
        "Total number of AI API requests",
        ["provider", "model", "operation"],
        registry=registry,
    )

    ai_tokens_total = Counter(
        "sophie_ai_tokens_total",
        "Total number of AI tokens consumed",
        ["provider", "model", "token_type"],
        registry=registry,
    )

    ai_tool_calls_total = Counter(
        "sophie_ai_tool_calls_total",
        "Total number of AI tool calls",
        ["tool_name", "status"],
        registry=registry,
    )

    ai_errors_total = Counter(
        "sophie_ai_errors_total",
        "Total number of AI operation errors",
        ["provider", "model", "error_type", "operation"],
        registry=registry,
    )

    ai_active_conversations = Gauge(
        "sophie_ai_active_conversations",
        "Number of active AI conversations",
        registry=registry,
    )

    ai_request_duration_seconds = Histogram(
        "sophie_ai_request_duration_seconds",
        "AI API request duration in seconds",
        ["provider", "model", "operation"],
        buckets=buckets,
        registry=registry,
    )

    ai_tool_duration_seconds = Histogram(
        "sophie_ai_tool_duration_seconds",
        "AI tool execution duration in seconds",
        ["tool_name"],
        buckets=buckets,
        registry=registry,
    )

    return SophieMetrics(
        updates_total=updates_total,
        messages_total=messages_total,
        handler_errors_total=handler_errors_total,
        external_errors_total=external_errors_total,
        inflight_handlers=inflight_handlers,
        event_loop_lag_seconds=event_loop_lag_seconds,
        handler_duration_seconds=handler_duration_seconds,
        external_request_duration_seconds=external_request_duration_seconds,
        build_info=build_info,
        # AI metrics
        ai_requests_total=ai_requests_total,
        ai_tokens_total=ai_tokens_total,
        ai_tool_calls_total=ai_tool_calls_total,
        ai_errors_total=ai_errors_total,
        ai_active_conversations=ai_active_conversations,
        ai_request_duration_seconds=ai_request_duration_seconds,
        ai_tool_duration_seconds=ai_tool_duration_seconds,
    )


def start_http_exporter(registry: CollectorRegistry, host: str, port: int) -> None:
    """Start HTTP server to expose metrics"""
    try:
        start_http_server(port, addr=host, registry=registry)
        log.info("Started Prometheus metrics exporter", host=host, port=port)
    except Exception as e:
        log.error("Failed to start metrics exporter", error=str(e))
        raise


def aiohttp_handler(registry: CollectorRegistry):
    """Create aiohttp handler for /metrics endpoint"""

    async def metrics_handler(request: web.Request) -> web.Response:
        """Handle metrics request"""
        try:
            data = generate_latest(registry)
            return web.Response(body=data, content_type=CONTENT_TYPE_LATEST, headers={"Cache-Control": "no-cache"})
        except Exception as e:
            log.error("Error generating metrics", error=str(e))
            return web.Response(text="Error generating metrics", status=500)

    return metrics_handler


# Optional pushgateway support (disabled by default per requirements)
def push_to_gateway(registry: CollectorRegistry, config: Any) -> None:
    """Push metrics to Pushgateway (optional, disabled by default)"""
    if not config.pushgateway_url:
        return

    try:
        from prometheus_client import push_to_gateway as push

        push(
            gateway=config.pushgateway_url,
            job=config.pushgateway_job,
            registry=registry,
            grouping_key={"instance": config.metrics_instance_id or socket.gethostname()},
        )
        log.debug("Pushed metrics to gateway", url=config.pushgateway_url)
    except ImportError:
        log.warning("prometheus_client pushgateway support not available")
    except Exception as e:
        log.error("Failed to push metrics to gateway", error=str(e))
