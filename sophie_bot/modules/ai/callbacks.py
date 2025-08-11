from aiogram.filters.callback_data import CallbackData


class AIResetContext(CallbackData, prefix="ai_reset_context"):
    pass


class AIProviderCallback(CallbackData, prefix="ai_provider"):
    provider: str  # 'openai' or 'google'


class AIPlaygroundCallback(CallbackData, prefix="ai_playground"):
    model: str  # specific model name like 'gpt_4o', 'gemini_2_5_flash', etc.


class AIChatCallback(CallbackData, prefix="ai_chat"):
    pass
