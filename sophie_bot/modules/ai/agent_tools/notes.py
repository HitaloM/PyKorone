from pydantic_ai import Tool


def notes_list_ai_tool():
    from sophie_bot.modules.ai.agent_tools._utils.get_chat_notes import AIChatNotesFunc

    return Tool(
        AIChatNotesFunc().__call__,
        name='get_notes',
        description='Get notes of the chat'
    )
