from __future__ import annotations

import asyncio
import sys
import time
from typing import Any, Optional

from sophie_bot.metrics.prom import SophieMetrics
from sophie_bot.utils.logger import log


async def start_background_tasks(metrics: SophieMetrics, config: Any) -> None:
    """Start background tasks for metrics collection"""

    # Set build info
    await _set_build_info(metrics)

    # Start event loop lag monitoring
    asyncio.create_task(_monitor_event_loop_lag(metrics))

    # Start periodic tasks if enabled
    if not config.metrics_light_mode:
        asyncio.create_task(_periodic_gauges(metrics))

    log.info("Started metrics background tasks")


async def _set_build_info(metrics: SophieMetrics) -> None:
    """Set build information metrics"""
    try:
        # Get version from pyproject.toml
        version = await _get_version_from_pyproject()

        # Get Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Get aiogram version
        try:
            import aiogram

            aiogram_version = aiogram.__version__
        except AttributeError:
            aiogram_version = "unknown"

        # Set build info
        metrics.build_info.info(
            {
                "version": version,
                "python": python_version,
                "aiogram_version": aiogram_version,
            }
        )

        log.debug("Set build info", version=version, python=python_version, aiogram=aiogram_version)

    except Exception as e:
        log.error("Failed to set build info", error=str(e))


async def _get_version_from_pyproject() -> str:
    """Get version from pyproject.toml"""
    try:
        import tomllib

        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "unknown")
    except Exception:
        # Fallback to reading as text file
        try:
            with open("pyproject.toml", "r") as f:
                for line in f:
                    if line.startswith("version ="):
                        version = line.split("=")[1].strip().strip('"').strip("'")
                        return version
        except Exception:
            pass

    return "unknown"


async def _monitor_event_loop_lag(metrics: SophieMetrics) -> None:
    """Monitor event loop lag and update gauge"""
    while True:
        try:
            # Measure event loop lag
            expected_sleep = 0.5
            start_time = time.perf_counter()

            await asyncio.sleep(expected_sleep)

            end_time = time.perf_counter()
            actual_sleep = end_time - start_time
            lag = max(0, actual_sleep - expected_sleep)

            # Update gauge
            metrics.event_loop_lag_seconds.set(lag)

            # Log excessive lag
            if lag > 1.0:
                log.warning("High event loop lag detected", lag_seconds=lag)
            elif lag > 0.1:
                log.debug("Event loop lag detected", lag_seconds=lag)

        except Exception as e:
            log.error("Error in event loop lag monitoring", error=str(e))
            # Continue monitoring even if there's an error
            await asyncio.sleep(1.0)


async def _periodic_gauges(metrics: SophieMetrics) -> None:
    """Update periodic gauge metrics (if not in light mode)"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes

            # Update connected chats count if available
            await _update_connected_chats_gauge(metrics)

        except Exception as e:
            log.error("Error in periodic gauges update", error=str(e))
            await asyncio.sleep(60)  # Retry after 1 minute on error


async def _update_connected_chats_gauge(metrics: SophieMetrics) -> None:
    """Update connected chats count gauge (optional)"""
    try:
        # This is optional and can be implemented later
        # For now, we'll skip this to keep the implementation simple
        # In the future, this could query the database for chat counts
        pass

    except Exception as e:
        log.error("Error updating connected chats gauge", error=str(e))


# Context manager for timing external services
class ExternalServiceTimer:
    """Context manager for timing external service calls"""

    def __init__(self, metrics: SophieMetrics, service_name: str) -> None:
        self.metrics = metrics
        self.service_name = service_name
        self.start_time: Optional[float] = None

    async def __aenter__(self) -> ExternalServiceTimer:
        self.start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time

            # Record duration
            self.metrics.external_request_duration_seconds.labels(service=self.service_name).observe(duration)

            # Record error if there was an exception
            if exc_type is not None:
                exception_name = exc_type.__name__ if exc_type else "unknown"
                self.metrics.external_errors_total.labels(service=self.service_name, exception=exception_name).inc()

                log.debug(
                    "External service error tracked",
                    service=self.service_name,
                    exception=exception_name,
                    duration=duration,
                )


def time_external(metrics: SophieMetrics, service_name: str) -> ExternalServiceTimer:
    """Create a context manager for timing external service calls"""
    return ExternalServiceTimer(metrics, service_name)
