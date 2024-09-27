from aiogram.filters.callback_data import CallbackData


class PMHelpModule(CallbackData, prefix="pmhelpmod"):
    module_name: str
    back_to_start: bool = False


class PMHelpModules(CallbackData, prefix="pmhelpback"):
    back_to_start: bool = False


class PMPrivacy(CallbackData, prefix="privacy"):
    back_to_start: bool = False
