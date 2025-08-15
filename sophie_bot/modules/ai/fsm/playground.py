from aiogram.fsm.state import State, StatesGroup


class AIPlaygroundFSM(StatesGroup):
    selected_model = State()


class AiPMFSM(StatesGroup):
    conversation = State()
