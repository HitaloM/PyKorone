from aiogram import Router

from sophie_bot.modules.notes.utils.legacy_notes import BUTTONS

router = Router(name="notes")


BUTTONS.update({"note": "btnnotesm", "#": "btnnotesm"})
