from aiogram.filters.callback_data import CallbackData

from sophie_bot.filters.command_start import CmdStart

PM_NOTES_REGEXP = r".*pm_notes_(?P<chat_id>(?:-)?\d+)"
PM_NOTES_TEMPLATE = "pm_notes_{chat_id}"


class PrivateNotesStartUrlCallback(CmdStart, prefix="pmnotes"):
    chat_id: int


class DeleteAllNotesCallback(CallbackData, prefix="delete_all_notes"):
    user_id: int
