from aiogram.fsm.state import State, StatesGroup


class ActionConfigFSM(StatesGroup):
    """FSM states for action configuration with interactive setup."""

    interactive_setup = State()
