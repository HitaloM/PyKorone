from aiogram.filters.callback_data import CallbackData


class PMHelpModule(CallbackData, prefix="pmhelpmod"):
    module_name: str
