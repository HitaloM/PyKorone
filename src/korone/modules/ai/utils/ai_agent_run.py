from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.usage import RunUsage  # noqa: TC002

from korone.utils.exception import KoroneError

from .ai_tool_context import KoroneAIToolContext
from .api import get_vulcan_openai_chat_model

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydantic_ai import Tool
    from pydantic_ai.messages import ModelMessage, UserContent

    from korone.middlewares.chat_context import ChatContext

    from .new_message_history import NewAIMessageHistory


class AIAgentResult[T](BaseModel):
    output: T
    message_history: list[ModelRequest | ModelResponse]
    usage: RunUsage


AIGenerateResult = AIAgentResult[str]


def _extract_model_messages(messages: Sequence[ModelMessage]) -> list[ModelRequest | ModelResponse]:
    return [message for message in messages if isinstance(message, (ModelRequest, ModelResponse))]


async def ai_agent_run[AgentDepsT, T](
    agent: Agent[AgentDepsT, T],
    *,
    user_prompt: str | Sequence[UserContent] | None = None,
    message_history: Sequence[ModelMessage] | None = None,
    deps: AgentDepsT,
) -> AIAgentResult[T]:
    try:
        result = await agent.run(user_prompt=user_prompt, message_history=message_history, deps=deps)
    except UnexpectedModelBehavior as exc:
        msg = "AI provider returned an invalid response. Please try again later."
        raise KoroneError(msg) from exc

    return AIAgentResult(
        output=result.output, message_history=_extract_model_messages(result.new_messages()), usage=result.usage()
    )


async def run_ai_prompt(
    history: NewAIMessageHistory, chat: ChatContext, tools: Sequence[Tool[KoroneAIToolContext]]
) -> AIGenerateResult:
    agent: Agent[KoroneAIToolContext, str] = Agent(
        get_vulcan_openai_chat_model(), deps_type=KoroneAIToolContext, tools=tools
    )
    result = await ai_agent_run(
        agent,
        user_prompt=history.prompt or None,
        message_history=history.message_history,
        deps=KoroneAIToolContext(chat=chat),
    )
    return result.model_copy(update={"output": str(result.output).strip() or "..."})
