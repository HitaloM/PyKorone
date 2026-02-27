from aiogram import Router
from stfu_tg import Doc

from korone.filters.admin_rights import UserRestricting as UserRestricting
from korone.filters.user_status import IsOP as IsOP
from korone.utils.i18n import LazyProxy as LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.admincache import ResetAdminCache
from .handlers.cancel import CancelState
from .handlers.cancel_callback import CallbackActionCancelHandler, CancelCallbackHandler, TypedCancelCallbackHandler

router = Router(name="troubleshooters")

__module_name__ = l_("Troubleshooters")
__module_emoji__ = "🧰"
__module_description__ = l_("Recovery and troubleshooting tools")
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Fix common state and permission cache issues when commands stop behaving as expected."),
        l_("Includes interaction reset and admin cache refresh tools."),
    )
)

__handlers__ = (
    CancelCallbackHandler,
    TypedCancelCallbackHandler,
    CallbackActionCancelHandler,
    ResetAdminCache,
    CancelState,
)
