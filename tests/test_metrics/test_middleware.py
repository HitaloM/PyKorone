from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, Update, User, Chat

from sophie_bot.metrics.middleware import MetricsMiddleware
from sophie_bot.metrics.prom import SophieMetrics


@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    config = MagicMock()
    config.metrics_enable = True
    config.metrics_sample_ratio = 1.0
    return config


@pytest.fixture
def mock_metrics():
    """Mock metrics for tests"""
    metrics = MagicMock(spec=SophieMetrics)

    # Mock counters
    metrics.updates_total = MagicMock()
    metrics.updates_total.labels.return_value.inc = MagicMock()

    metrics.messages_total = MagicMock()
    metrics.messages_total.labels.return_value.inc = MagicMock()

    metrics.handler_errors_total = MagicMock()
    metrics.handler_errors_total.labels.return_value.inc = MagicMock()

    # Mock gauges
    metrics.inflight_handlers = MagicMock()
    metrics.inflight_handlers.inc = MagicMock()
    metrics.inflight_handlers.dec = MagicMock()

    # Mock histograms
    metrics.handler_duration_seconds = MagicMock()
    metrics.handler_duration_seconds.labels.return_value.observe = MagicMock()

    return metrics


@pytest.fixture
def middleware(mock_metrics, mock_config):
    """Create middleware instance for tests"""
    return MetricsMiddleware(mock_metrics, mock_config)


@pytest.fixture
def mock_message():
    """Mock message for tests"""
    from datetime import datetime

    user = User(id=123, is_bot=False, first_name="Test")
    chat = Chat(id=456, type="private")
    return Message(message_id=1, date=datetime.now(), chat=chat, from_user=user, text="Hello world")


@pytest.fixture
def mock_update(mock_message):
    """Mock update for tests"""
    return Update(update_id=1, message=mock_message)


class TestMetricsMiddleware:
    """Test suite for MetricsMiddleware"""

    @pytest.mark.asyncio
    async def test_successful_handler_execution(
        self, middleware: MetricsMiddleware, mock_update: Update, mock_metrics: MagicMock
    ):
        """Test successful handler execution metrics"""
        handler = AsyncMock(return_value="success")
        data = {}

        result = await middleware(handler, mock_update, data)

        # Check that handler was called
        handler.assert_called_once_with(mock_update, data)
        assert result == "success"

        # Check metrics were recorded
        mock_metrics.updates_total.labels.assert_called_once()
        mock_metrics.messages_total.labels.assert_called_once()
        mock_metrics.inflight_handlers.inc.assert_called_once()
        mock_metrics.inflight_handlers.dec.assert_called_once()
        mock_metrics.handler_duration_seconds.labels.assert_called_once()

        # Check no error metrics
        mock_metrics.handler_errors_total.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_handler_exception(self, middleware: MetricsMiddleware, mock_update: Update, mock_metrics: MagicMock):
        """Test handler exception handling and error metrics"""
        test_exception = ValueError("Test error")
        handler = AsyncMock(side_effect=test_exception)
        data = {}

        with pytest.raises(ValueError, match="Test error"):
            await middleware(handler, mock_update, data)

        # Check error metrics were recorded
        mock_metrics.handler_errors_total.labels.assert_called_once()
        error_labels = mock_metrics.handler_errors_total.labels.call_args[1]
        assert error_labels["exception"] == "ValueError"

        # Check inflight handlers were decremented
        mock_metrics.inflight_handlers.dec.assert_called_once()

        # Check duration was still recorded
        mock_metrics.handler_duration_seconds.labels.assert_called_once()

    @pytest.mark.asyncio
    async def test_sampling_skip(self, mock_metrics: MagicMock, mock_config: MagicMock, mock_update: Update):
        """Test that sampling works correctly"""
        mock_config.metrics_sample_ratio = 0.0  # Always skip
        middleware = MetricsMiddleware(mock_metrics, mock_config)

        handler = AsyncMock(return_value="success")
        data = {}

        with patch("random.random", return_value=0.5):
            result = await middleware(handler, mock_update, data)

        # Handler should still be called
        handler.assert_called_once_with(mock_update, data)
        assert result == "success"

        # But no metrics should be recorded
        mock_metrics.updates_total.labels.assert_not_called()
        mock_metrics.messages_total.labels.assert_not_called()

    def test_extract_update_info_message(self, middleware: MetricsMiddleware, mock_update: Update):
        """Test update info extraction for messages"""
        info = middleware._extract_update_info(mock_update, {})

        assert info["update_type"] == "message"
        assert info["chat_type"] == "private"
        assert info["transport"] == "polling"
        assert info["message_kind"] == "text"

    def test_extract_update_info_callback_query(self, middleware: MetricsMiddleware, mock_message: Message):
        """Test update info extraction for callback queries"""
        from aiogram.types import CallbackQuery

        callback_query = CallbackQuery(
            id="test",
            from_user=User(id=123, is_bot=False, first_name="Test"),
            chat_instance="test",
            message=mock_message,
            data="test_data",
        )
        update = Update(update_id=1, callback_query=callback_query)

        info = middleware._extract_update_info(update, {})

        assert info["update_type"] == "callback_query"
        assert info["chat_type"] == "private"
        assert info["message_kind"] is None

    def test_get_message_kind_text(self, middleware: MetricsMiddleware, mock_message: Message):
        """Test message kind extraction for text messages"""
        kind = middleware._get_message_kind(mock_message)
        assert kind == "text"

    def test_get_message_kind_photo(self, middleware: MetricsMiddleware):
        """Test message kind extraction for photo messages"""
        from aiogram.types import PhotoSize
        from datetime import datetime

        user = User(id=123, is_bot=False, first_name="Test")
        chat = Chat(id=456, type="private")
        photo = [PhotoSize(file_id="test", file_unique_id="test", width=100, height=100)]

        message = Message(message_id=1, date=datetime.now(), chat=chat, from_user=user, photo=photo)

        kind = middleware._get_message_kind(message)
        assert kind == "photo"

    def test_get_handler_name(self, middleware: MetricsMiddleware):
        """Test handler name extraction"""

        # Test with function name
        def test_handler():
            pass

        name = middleware._get_handler_name(test_handler, None)
        assert name == "test_handler"

        # Test with class method (should return class name, not method name)
        class TestHandler:
            def handle(self):
                pass

        handler_instance = TestHandler()
        name = middleware._get_handler_name(handler_instance.handle, None)
        assert name == "TestHandler"  # Expect class name, not method name

        # Test with functools.partial (common with aiogram class-based handlers)
        from functools import partial

        class AiPmStop:
            def handle(self):
                pass

        handler_instance = AiPmStop()
        partial_handler = partial(handler_instance.handle)
        name = middleware._get_handler_name(partial_handler, None)
        assert name == "AiPmStop"  # Should extract class name from partial

        # Test middleware object with memory address (the main issue we're fixing)
        class MockMiddleware:
            def __call__(self):
                pass  # Make it callable

            def __str__(self):
                return "<sophie_bot.middlewares.connections.ConnectionsMiddleware object at 0x7fa6c518c380>"

        mock_middleware = MockMiddleware()
        name = middleware._get_handler_name(mock_middleware, None)
        assert name == "ConnectionsMiddleware"  # Should extract clean class name

        # Test another middleware object format
        class MockMiddleware2:
            def __call__(self):
                pass

            def __str__(self):
                return "<MyCustomMiddleware object at 0x12345678>"

        mock_middleware2 = MockMiddleware2()
        name2 = middleware._get_handler_name(mock_middleware2, None)
        assert name2 == "MyCustomMiddleware"

        # Test name length limit
        long_name = "a" * 60
        setattr(test_handler, "__name__", long_name)
        name = middleware._get_handler_name(test_handler, None)
        assert len(name) == 50

    def test_webhook_transport_detection(self, middleware: MetricsMiddleware, mock_update: Update):
        """Test webhook transport detection"""
        data = {"webhook_info": True}
        info = middleware._extract_update_info(mock_update, data)
        assert info["transport"] == "webhook"

    @pytest.mark.asyncio
    async def test_concurrent_handlers(
        self, middleware: MetricsMiddleware, mock_update: Update, mock_metrics: MagicMock
    ):
        """Test that concurrent handlers are tracked correctly"""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        # Simulate slow handlers
        async def slow_handler1(*args, **kwargs):
            await asyncio.sleep(0.1)
            return "result1"

        async def slow_handler2(*args, **kwargs):
            await asyncio.sleep(0.1)
            return "result2"

        handler1.side_effect = slow_handler1
        handler2.side_effect = slow_handler2

        # Run handlers concurrently
        results = await asyncio.gather(middleware(handler1, mock_update, {}), middleware(handler2, mock_update, {}))

        assert results == ["result1", "result2"]

        # Check that inflight handlers were incremented twice
        assert mock_metrics.inflight_handlers.inc.call_count == 2
        # And decremented twice
        assert mock_metrics.inflight_handlers.dec.call_count == 2
