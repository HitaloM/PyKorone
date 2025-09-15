from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from sophie_bot.metrics import track_ai_request, track_ai_usage

T = TypeVar("T")


class AIAgentResult(Generic[T], BaseModel):
    output: T
    steps: int
    retries: int
    message_history: list[ModelRequest | ModelResponse]
    usage: RunUsage


async def ai_agent_run(agent: Agent[None, T], **kwargs) -> AIAgentResult:
    # Extract model for metrics tracking
    model = agent.model

    # Ensure model is not None for metrics tracking
    if model is None:
        raise ValueError("Agent model cannot be None for metrics tracking")

    # Ensure model is a Model instance for metrics tracking
    if not isinstance(model, Model):
        raise ValueError(f"Agent model must be a Model instance, got {type(model)}")

    async with track_ai_request(model, "agent"):
        async with agent.iter(**kwargs) as result:
            async for _ in result:
                pass

        # Sanity checks
        assert result and result.result is not None, "The graph run did not finish properly"

        context = result.ctx
        state = context.state

        # Track token usage
        if state.usage:
            track_ai_usage(model, state.usage)

        return AIAgentResult(
            output=result.result.output,
            steps=state.run_step,
            retries=state.retries,
            message_history=state.message_history,
            usage=state.usage,
        )
