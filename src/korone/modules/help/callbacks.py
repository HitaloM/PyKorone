from aiogram.filters.callback_data import CallbackData

HELP_START_PAYLOAD = "help"


class PMHelpModule(CallbackData, prefix="pmhelpmod"):
    module_name: str
    back_to_start: bool = False


class PMHelpModules(CallbackData, prefix="pmhelpback"):
    back_to_start: bool = False
