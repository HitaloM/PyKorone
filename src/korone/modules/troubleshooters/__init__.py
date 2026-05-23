from aiogram import Router
from stfu_tg import Doc

from korone.filters.admin_rights import UserRestricting as UserRestricting
from korone.filters.user_status import IsOP as IsOP
from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy as LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.admincache import ResetAdminCache
from .handlers.cancel import CancelState
from .handlers.cancel_callback import CallbackActionCancelHandler, CancelCallbackHandler, TypedCancelCallbackHandler

router = Router(name="troubleshooters")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Troubleshooters"),
        icon="🧰",
        summary=l_("Recovery and troubleshooting tools"),
        description=LazyProxy(
            lambda: Doc(
                l_("Fix common state and permission cache issues when commands stop behaving as expected."),
                l_("Includes interaction reset and admin cache refresh tools."),
            )
        ),
    ),
    router=router,
    handlers=(
        CancelCallbackHandler,
        TypedCancelCallbackHandler,
        CallbackActionCancelHandler,
        ResetAdminCache,
        CancelState,
    ),
)
