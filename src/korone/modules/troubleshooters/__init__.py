from aiogram import Router

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
__module_description__ = l_("Tools for fixing problems and issues")

__handlers__ = (
    CancelCallbackHandler,
    TypedCancelCallbackHandler,
    CallbackActionCancelHandler,
    ResetAdminCache,
    CancelState,
)
