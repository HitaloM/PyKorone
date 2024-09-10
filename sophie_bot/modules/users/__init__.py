import importlib

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from .stats import users_stats

__stats__ = users_stats

router = Router(name="users")


__module_name__ = l_("Users")
__module_emoji__ = "🫂"


def __pre_setup__():
    router.include_router(importlib.import_module(".handlers.id", __package__).router)
