from aiogram.fsm.state import State, StatesGroup


class NewFilterFSM(StatesGroup):
    action_setup = State()
    action_edit = State()
