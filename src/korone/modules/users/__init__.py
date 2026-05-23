from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .handlers.adminlist import AdminListHandler
from .handlers.id import ShowIDHandler
from .handlers.info import UserInfoHandler
from .stats import users_stats

router = Router(name="users")
manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Users"),
        icon="🫂",
        summary=l_("User and member lookup tools"),
        description=LazyProxy(
            lambda: Doc(
                l_("Inspect IDs, chat admins, and detailed user information."),
                l_("Works with replies, direct users, and explicit mentions."),
            )
        ),
    ),
    router=router,
    handlers=(ShowIDHandler, AdminListHandler, UserInfoHandler),
    stats=users_stats,
)
