from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from ...filters.admin_rights import UserRestricting as UserRestricting
from ...filters.user_status import IsOP as IsOP
from .handlers.admincache import ResetAdminCache
from .handlers.cancel import CancelState
from .handlers.cancel_callback import CallbackActionCancelHandler, CancelCallbackHandler, TypedCancelCallbackHandler

router = Router(name="troubleshooters")

__module_name__ = l_("Troubleshooters")
__module_emoji__ = "🧰"
__module_info__ = l_("Small commands for fixing problems and issues")
__module_info__ = LazyProxy(lambda: Doc(l_("Fix common problems and issues you might encounter while using the bot.")))

__handlers__ = (
    CancelCallbackHandler,
    TypedCancelCallbackHandler,
    CallbackActionCancelHandler,
    ResetAdminCache,
    CancelState,
)
