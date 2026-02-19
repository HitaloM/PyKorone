from aiogram.filters.callback_data import CallbackData


class AIResetContext(CallbackData, prefix="ai_reset_context"):
    pass


class AIChatCallback(CallbackData, prefix="ai_chat"):
    pass
