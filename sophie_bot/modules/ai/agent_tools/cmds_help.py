from pydantic_ai import RunContext, Tool

from sophie_bot.modules.ai.utils.ai_tool_context import SophieAIToolContenxt
from sophie_bot.modules.help.utils.extract_info import get_all_cmds
from sophie_bot.modules.help.utils.format_help import group_handlers
from sophie_bot.metrics import track_ai_tool


class CmdsHelpAgentTool:
    @staticmethod
    async def tool_call(ctx: RunContext[SophieAIToolContenxt]) -> str:
        """Extract and format all command help information for AI context"""
        async with track_ai_tool("cmds_help"):
            all_cmds = get_all_cmds()

            if not all_cmds:
                return "No commands available."

            # Group commands by type
            grouped_handlers = group_handlers(all_cmds)

            # Format for AI consumption
            help_text = "Available Sophie Bot Commands:\n\n"

            for group_name, handlers in grouped_handlers:
                help_text += f"--- {group_name} ---\n"

                for handler in handlers:
                    # Format command names
                    cmds_str = ", ".join(f"/{cmd}" for cmd in handler.cmds)
                    help_text += f"• {cmds_str}"

                    # Add arguments if present
                    if handler.args:
                        args_str = " ".join(f"<{arg.description}>" for arg in handler.args.values())
                        help_text += f" {args_str}"

                    # Add description if present
                    if handler.description:
                        help_text += f" - {handler.description}"

                    # Add special conditions
                    conditions = []
                    if handler.only_admin:
                        conditions.append("admin only")
                    if handler.only_pm:
                        conditions.append("PM only")
                    if handler.only_chats:
                        conditions.append("groups only")
                    if handler.disableable:
                        conditions.append(f"disableable as '{handler.disableable}'")

                    if conditions:
                        help_text += f" [{', '.join(conditions)}]"

                    help_text += "\n"

                help_text += "\n"

            return help_text.strip()

    def __new__(cls):
        return Tool(
            cls.tool_call,
            name="cmds_help",
            description="Get information about all available bot commands and their usage",
            takes_ctx=True,
        )
