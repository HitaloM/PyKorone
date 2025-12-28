from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch
import pytest

from sophie_bot.metrics.external import (
    ExternalServiceTracker,
    create_service_tracker,
    instrument_external_service,
    instrument_mongo,
    instrument_openai,
    instrument_redis,
    set_metrics,
    time_external_service,
)


@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    config = MagicMock()
    config.metrics_enable = True
    return config


@pytest.fixture
def mock_metrics():
    """Mock metrics for tests"""
    metrics = MagicMock()

    # Mock external service metrics
    metrics.external_request_duration_seconds = MagicMock()
    metrics.external_request_duration_seconds.labels.return_value.observe = MagicMock()

    metrics.external_errors_total = MagicMock()
    metrics.external_errors_total.labels.return_value.inc = MagicMock()

    return metrics


@pytest.fixture(autouse=True)
def setup_metrics(mock_metrics, mock_config):
    """Set up metrics for all tests"""
    with patch("sophie_bot.metrics.external.CONFIG", mock_config):
        set_metrics(mock_metrics)
        yield
        # Reset global state
        set_metrics(None)


class TestExternalServiceInstrumentation:
    """Test suite for external service instrumentation"""

    @pytest.mark.asyncio
    async def test_time_external_service_success(self, mock_metrics: MagicMock):
        """Test successful external service timing"""
        async with time_external_service("test_service"):
            await asyncio.sleep(0.01)  # Simulate some work

        # Check that duration was recorded
        mock_metrics.external_request_duration_seconds.labels.assert_called_once_with(service="test_service")
        mock_metrics.external_request_duration_seconds.labels.return_value.observe.assert_called_once()

        # Check that no error was recorded
        mock_metrics.external_errors_total.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_time_external_service_exception(self, mock_metrics: MagicMock):
        """Test external service timing with exception"""
        test_exception = ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            async with time_external_service("test_service"):
                raise test_exception

        # Check that duration was recorded
        mock_metrics.external_request_duration_seconds.labels.assert_called_once_with(service="test_service")
        mock_metrics.external_request_duration_seconds.labels.return_value.observe.assert_called_once()

        # Check that error was recorded
        mock_metrics.external_errors_total.labels.assert_called_once_with(
            service="test_service", exception="ValueError"
        )
        mock_metrics.external_errors_total.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_time_external_service_disabled(self, mock_config: MagicMock, mock_metrics: MagicMock):
        """Test that timing is skipped when metrics are disabled"""
        mock_config.metrics_enable = False

        async with time_external_service("test_service"):
            await asyncio.sleep(0.01)

        # No metrics should be recorded
        mock_metrics.external_request_duration_seconds.labels.assert_not_called()
        mock_metrics.external_errors_total.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_instrument_external_service_async(self, mock_metrics: MagicMock):
        """Test decorator on async functions"""

        @instrument_external_service("test_service")
        async def test_async_function():
            await asyncio.sleep(0.01)
            return "success"

        result = await test_async_function()
        assert result == "success"

        # Check metrics were recorded
        mock_metrics.external_request_duration_seconds.labels.assert_called_once_with(service="test_service")
        mock_metrics.external_request_duration_seconds.labels.return_value.observe.assert_called_once()

    def test_instrument_external_service_sync(self, mock_metrics: MagicMock):
        """Test decorator on sync functions"""

        @instrument_external_service("test_service")
        def test_sync_function():
            return "success"

        result = test_sync_function()
        assert result == "success"

        # Check metrics were recorded
        mock_metrics.external_request_duration_seconds.labels.assert_called_once_with(service="test_service")
        mock_metrics.external_request_duration_seconds.labels.return_value.observe.assert_called_once()

    @pytest.mark.asyncio
    async def test_instrument_external_service_async_exception(self, mock_metrics: MagicMock):
        """Test decorator on async functions with exception"""

        @instrument_external_service("test_service")
        async def test_async_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await test_async_function()

        # Check error metrics were recorded
        mock_metrics.external_errors_total.labels.assert_called_once_with(
            service="test_service", exception="ValueError"
        )

    def test_instrument_external_service_sync_exception(self, mock_metrics: MagicMock):
        """Test decorator on sync functions with exception"""

        @instrument_external_service("test_service")
        def test_sync_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_sync_function()

        # Check error metrics were recorded
        mock_metrics.external_errors_total.labels.assert_called_once_with(
            service="test_service", exception="ValueError"
        )

    @pytest.mark.asyncio
    async def test_specific_service_decorators(self, mock_metrics: MagicMock):
        """Test specific service decorators"""

        @instrument_mongo("find")
        async def mongo_operation():
            return "mongo_result"

        @instrument_redis("get")
        async def redis_operation():
            return "redis_result"

        @instrument_openai("completion")
        async def openai_operation():
            return "openai_result"

        # Test each decorator
        result = await mongo_operation()
        assert result == "mongo_result"

        result = await redis_operation()
        assert result == "redis_result"

        result = await openai_operation()
        assert result == "openai_result"

        # Check that correct service names were used
        expected_services = ["mongo_find", "redis_get", "openai_completion"]

        actual_calls = mock_metrics.external_request_duration_seconds.labels.call_args_list
        for i, expected_service in enumerate(expected_services):
            assert actual_calls[i][1]["service"] == expected_service


class TestExternalServiceTracker:
    """Test suite for manual external service tracking"""

    def test_tracker_success(self, mock_metrics: MagicMock):
        """Test manual tracker for successful operation"""
        tracker = create_service_tracker("manual_service")

        tracker.start()
        # Simulate some work
        import time

        time.sleep(0.001)
        tracker.finish()

        # Check metrics were recorded
        mock_metrics.external_request_duration_seconds.labels.assert_called_once_with(service="manual_service")
        mock_metrics.external_request_duration_seconds.labels.return_value.observe.assert_called_once()

        # Check no error was recorded
        mock_metrics.external_errors_total.labels.assert_not_called()

    def test_tracker_with_exception(self, mock_metrics: MagicMock):
        """Test manual tracker with exception"""
        tracker = create_service_tracker("manual_service")
        test_exception = ValueError("Test error")

        tracker.start()
        tracker.finish(test_exception)

        # Check duration was recorded
        mock_metrics.external_request_duration_seconds.labels.assert_called_once_with(service="manual_service")
        mock_metrics.external_request_duration_seconds.labels.return_value.observe.assert_called_once()

        # Check error was recorded
        mock_metrics.external_errors_total.labels.assert_called_once_with(
            service="manual_service", exception="ValueError"
        )
        mock_metrics.external_errors_total.labels.return_value.inc.assert_called_once()

    def test_tracker_without_start(self, mock_metrics: MagicMock):
        """Test tracker finish without start (should not crash)"""
        tracker = create_service_tracker("manual_service")

        # Finish without start should not record anything
        tracker.finish()

        # No metrics should be recorded
        mock_metrics.external_request_duration_seconds.labels.assert_not_called()
        mock_metrics.external_errors_total.labels.assert_not_called()

    def test_tracker_disabled_metrics(self, mock_config: MagicMock, mock_metrics: MagicMock):
        """Test tracker when metrics are disabled"""
        mock_config.metrics_enable = False

        tracker = create_service_tracker("manual_service")
        tracker.start()
        tracker.finish()

        # No metrics should be recorded
        mock_metrics.external_request_duration_seconds.labels.assert_not_called()


class TestServiceIntegration:
    """Test service-specific integration helpers"""

    @pytest.mark.asyncio
    async def test_service_context_managers(self, mock_metrics: MagicMock):
        """Test service-specific context managers"""
        from sophie_bot.metrics.external import (
            time_mongo_operation,
            time_redis_operation,
            time_openai_operation,
            time_telegram_api_operation,
        )

        # Test each context manager
        async with time_mongo_operation("find"):
            pass

        async with time_redis_operation("set"):
            pass

        async with time_openai_operation("chat"):
            pass

        async with time_telegram_api_operation("send_message"):
            pass

        # Check correct service names were used
        expected_services = ["mongo_find", "redis_set", "openai_chat", "telegram_send_message"]

        actual_calls = mock_metrics.external_request_duration_seconds.labels.call_args_list
        for expected_service, call in zip(expected_services, actual_calls):
            assert call[1]["service"] == expected_service

    def test_set_metrics_function(self):
        """Test setting metrics globally"""
        test_metrics = MagicMock()

        set_metrics(test_metrics)

        # The global _metrics should be set
        from sophie_bot.metrics.external import _metrics

        assert _metrics is test_metrics

    def test_create_service_tracker_type(self):
        """Test that create_service_tracker returns correct type"""
        tracker = create_service_tracker("test")
        assert isinstance(tracker, ExternalServiceTracker)
        assert tracker.service_name == "test"
