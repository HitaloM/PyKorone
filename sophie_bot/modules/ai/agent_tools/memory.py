from pydantic_ai import RunContext, Tool

from sophie_bot.db.models.ai.ai_memory import AIMemoryModel
from sophie_bot.modules.ai.utils.ai_tool_context import SophieAIToolContenxt
from sophie_bot.metrics import track_ai_tool


class MemoryAgentTool:
    @staticmethod
    async def tool_call(ctx: RunContext[SophieAIToolContenxt], information_to_save: str):
        async with track_ai_tool("write_memory"):
            await AIMemoryModel.append_line(ctx.deps.connection.db_model, information_to_save)

    def __new__(cls):
        return Tool(
            cls.tool_call, name="write_memory", description="Save information to the long term memory", takes_ctx=True
        )
