from aiogram.filters.callback_data import CallbackData

from korone.filters.command_start import CmdStart


class PMHelpModule(CallbackData, prefix="pmhelpmod"):
    module_name: str
    back_to_start: bool = False


class PMHelpModules(CallbackData, prefix="pmhelpback"):
    back_to_start: bool = False


class PMHelpStartUrlCallback(CmdStart, prefix="help"):
    pass
