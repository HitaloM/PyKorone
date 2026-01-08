from aiogram import Router
from sophie_bot.modules.locks.handlers.lockable import ListLockableHandler

from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Locks")
__module_emoji__ = "🔓"

router = Router(name="locks")

__handlers__ = ListLockableHandler
