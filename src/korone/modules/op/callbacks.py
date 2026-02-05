from aiogram.filters.callback_data import CallbackData


class OpUpdateCallback(CallbackData, prefix="op_update"):
    initiator_id: int


class OpRestartCallback(CallbackData, prefix="op_restart"):
    initiator_id: int
