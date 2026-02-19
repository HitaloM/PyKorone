from __future__ import annotations

from pydantic_ai import RunContext, Tool  # noqa: TC002

from korone.modules.ai.utils.ai_tool_context import KoroneAIToolContext  # noqa: TC001
from korone.modules.ai.utils.memory import append_memory_line


class MemoryAgentTool:
    @staticmethod
    async def tool_call(ctx: RunContext[KoroneAIToolContext], information_to_save: str) -> None:
        await append_memory_line(ctx.deps.chat_id, information_to_save)

    def __new__(cls) -> Tool[KoroneAIToolContext]:
        return Tool(
            cls.tool_call, name="write_memory", description="Save information to long-term memory.", takes_ctx=True
        )
