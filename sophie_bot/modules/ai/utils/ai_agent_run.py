from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.usage import Usage


class AIAgentResult(BaseModel):
    output: str
    steps: int
    retires: int
    message_history: list[ModelRequest | ModelResponse]
    usage: Usage


async def ai_agent_run(agent: Agent, **kwargs) -> AIAgentResult:
    async with agent.iter(**kwargs) as result:
        async for _ in result:
            pass

    # Sanity checks
    assert result and result.result is not None, "The graph run did not finish properly"

    context = result.ctx
    state = context.state

    return AIAgentResult(
        output=result.result.data,
        steps=state.run_step,
        retires=state.retries,
        message_history=state.message_history,
        usage=state.usage,
    )
