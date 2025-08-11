from aiogram.fsm.state import State, StatesGroup


class AIPlaygroundFSM(StatesGroup):
    selected_model = State()


class AiPMFSM(StatesGroup):
    conversation = State()


# Constants for other modules
AI_GENERATED_TEXT = "ai_generated_text"
AI_PM_RESET = "ai_pm_reset"
AI_PM_STOP_TEXT = "ai_pm_stop_text"
