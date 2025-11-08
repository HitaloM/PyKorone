from aiogram import Router

from sophie_bot.modules.notes.utils.buttons_processor.legacy import BUTTONS
from sophie_bot.modes import SOPHIE_MODE
from sophie_bot.services.scheduler import scheduler
from sophie_bot.modules.welcomesecurity.handlers.captcha_confirm import (
    CaptchaConfirmHandler,
)
from sophie_bot.modules.welcomesecurity.handlers.captcha_get import CaptchaGetHandler
from sophie_bot.modules.welcomesecurity.handlers.chat_join_request import (
    ChatJoinRequestHandler,
)
from sophie_bot.modules.welcomesecurity.handlers.enable_welcomemute import (
    EnableWelcomeMute,
)
from sophie_bot.modules.welcomesecurity.handlers.enable_ws import (
    EnableWelcomeCaptchaHandlerABC,
)
from sophie_bot.modules.welcomesecurity.handlers.legacy_button import (
    LegacyStableWSButtonRedirectHandler,
    LegacyWSButtonHandler,
)
from sophie_bot.modules.welcomesecurity.handlers.status_overall import (
    WelcomeSecuritySettingsShowHandler,
)
from sophie_bot.modules.welcomesecurity.middlewares.lock_muted_users import (
    LockMutedUsers,
)
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Welcome Security")
__module_emoji__ = "🛡️"
__module_info__ = l_(
    "Welcome Security contains a bunch of tools that can help filter bots that tries to join your groups, as well as make sure the new users acknowledged the chat rules before being able to speak"
)

router = Router(name="welcomesecurity")


BUTTONS.update({"welcomesecurity": "btnwelcomesecuritystart"})


__handlers__ = (
    CaptchaGetHandler,
    LegacyWSButtonHandler,
    CaptchaConfirmHandler,
    ChatJoinRequestHandler,
    EnableWelcomeCaptchaHandlerABC,
    EnableWelcomeMute,
    WelcomeSecuritySettingsShowHandler,
    LegacyStableWSButtonRedirectHandler,
)


async def __pre_setup__():
    router.message.outer_middleware(LockMutedUsers())


async def __post_setup__(_):
    if SOPHIE_MODE == "scheduler":
        from sophie_bot.modules.welcomesecurity.schedules.ban_unpassed_users import BanUnpassedUsers

        scheduler.add_job(BanUnpassedUsers().handle, "interval", minutes=10, jobstore="ram")
