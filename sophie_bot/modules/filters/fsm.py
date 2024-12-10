from aiogram.fsm.state import State, StatesGroup


class FilterEditFSM(StatesGroup):
    action_setup = State()
    action_change_settings = State()
    action_edit = State()
    handler_edit = State()
