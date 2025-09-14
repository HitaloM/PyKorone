from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from sophie_bot.config import CONFIG
from sophie_bot.utils.logger import log

# Global metrics instance - will be set during initialization
_metrics = None


def set_ai_metrics(metrics) -> None:
    """Set the global metrics instance for AI instrumentation"""
    global _metrics
    _metrics = metrics
    log.info("AI metrics instrumentation enabled")


def get_provider_from_model(model: Model) -> str:
    """Extract provider name from AI model"""
    # Extract provider name from the model's provider attribute
    if hasattr(model, "provider") and model.provider:
        provider_class_name = model.provider.__class__.__name__
        # Convert provider class names to simple provider names
        if "OpenAI" in provider_class_name:
            return "openai"
        elif "Google" in provider_class_name:
            return "google"
        elif "Mistral" in provider_class_name:
            return "mistral"

    # Fallback: try to infer from model name
    model_name = model.model_name.lower()
    if "gpt" in model_name or "openai" in model_name:
        return "openai"
    elif "gemini" in model_name or "google" in model_name:
        return "google"
    elif "mistral" in model_name or "codestral" in model_name or "pixtral" in model_name:
        return "mistral"

    return "unknown"


def get_model_name(model: Model) -> str:
    """Extract model name for metrics labeling"""
    return model.model_name


@asynccontextmanager
async def track_ai_request(model: Model, operation: str = "chat") -> AsyncGenerator[None, None]:
    """Context manager for tracking AI API requests"""
    if not _metrics or not CONFIG.metrics_enable:
        yield
        return

    provider = get_provider_from_model(model)
    model_name = get_model_name(model)
    start_time = time.perf_counter()

    # Increment request counter
    _metrics.ai_requests_total.labels(provider=provider, model=model_name, operation=operation).inc()

    error_type = "unknown"

    try:
        yield
    except Exception as e:
        error_type = type(e).__name__

        # Track AI errors
        _metrics.ai_errors_total.labels(
            provider=provider, model=model_name, error_type=error_type, operation=operation
        ).inc()

        log.debug(
            "AI request error tracked", provider=provider, model=model_name, operation=operation, error=error_type
        )
        raise
    finally:
        # Record request duration
        duration = time.perf_counter() - start_time
        _metrics.ai_request_duration_seconds.labels(provider=provider, model=model_name, operation=operation).observe(
            duration
        )


def track_ai_usage(model: Model, usage: RunUsage) -> None:
    """Track AI token usage metrics"""
    if not _metrics or not CONFIG.metrics_enable:
        return

    provider = get_provider_from_model(model)
    model_name = get_model_name(model)

    # Track different token types
    if usage.request_tokens:
        _metrics.ai_tokens_total.labels(provider=provider, model=model_name, token_type="request").inc(
            usage.request_tokens
        )

    if usage.response_tokens:
        _metrics.ai_tokens_total.labels(provider=provider, model=model_name, token_type="response").inc(
            usage.response_tokens
        )

    if usage.total_tokens:
        _metrics.ai_tokens_total.labels(provider=provider, model=model_name, token_type="total").inc(usage.total_tokens)


@asynccontextmanager
async def track_ai_tool(tool_name: str) -> AsyncGenerator[None, None]:
    """Context manager for tracking AI tool calls"""
    if not _metrics or not CONFIG.metrics_enable:
        yield
        return

    start_time = time.perf_counter()
    status = "success"

    try:
        yield
    except Exception as e:
        status = "error"
        log.debug("AI tool error tracked", tool=tool_name, error=type(e).__name__)
        raise
    finally:
        # Track tool call
        _metrics.ai_tool_calls_total.labels(tool_name=tool_name, status=status).inc()

        # Track tool duration
        duration = time.perf_counter() - start_time
        _metrics.ai_tool_duration_seconds.labels(tool_name=tool_name).observe(duration)


def track_active_conversation_start() -> None:
    """Track the start of an AI conversation"""
    if not _metrics or not CONFIG.metrics_enable:
        return

    _metrics.ai_active_conversations.inc()


def track_active_conversation_end() -> None:
    """Track the end of an AI conversation"""
    if not _metrics or not CONFIG.metrics_enable:
        return

    _metrics.ai_active_conversations.dec()


class AIConversationTracker:
    """Context manager for tracking active AI conversations"""

    def __init__(self):
        self.tracked = False

    async def __aenter__(self):
        if _metrics and CONFIG.metrics_enable:
            track_active_conversation_start()
            self.tracked = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.tracked:
            track_active_conversation_end()


def track_ai_conversation():
    """Create an AI conversation tracker context manager"""
    return AIConversationTracker()


# Decorator for AI operations
def instrument_ai_operation(operation: str = "chat"):
    """Decorator for AI operations that need metrics tracking"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Try to extract model from arguments
            model = None
            for arg in args:
                if isinstance(arg, Model):
                    model = arg
                    break

            # Try to extract from kwargs
            if not model:
                model = kwargs.get("model")

            if model and _metrics and CONFIG.metrics_enable:
                async with track_ai_request(model, operation):
                    result = await func(*args, **kwargs)

                    # If result has usage info, track it
                    if hasattr(result, "usage") and result.usage:
                        track_ai_usage(model, result.usage)

                    return result
            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
