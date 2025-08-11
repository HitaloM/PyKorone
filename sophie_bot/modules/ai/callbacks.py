from aiogram.filters.callback_data import CallbackData


class AIResetContext(CallbackData, prefix="ai_reset_context"):
    pass


class AIProviderCallback(CallbackData, prefix="ai_provider"):
    provider: str  # 'openai' or 'google'
