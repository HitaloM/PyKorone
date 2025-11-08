from aiogram import Router

from sophie_bot.modules.greetings.handlers.enablewelcome import EnableWelcomeHandlerABC
from sophie_bot.modules.greetings.handlers.status_cleanservice import (
    CleanServiceHandlerABC,
)
from sophie_bot.modules.greetings.handlers.status_cleanwelcome import (
    CleanWelcomeHandlerABC,
)
from sophie_bot.modules.greetings.handlers.set_join_request import (
    DelJoinRequestMessageHandler,
    SetJoinRequestMessageHandler,
)
from sophie_bot.modules.greetings.handlers.status_greetings import (
    SetWelcomeMessageHandler,
)
from sophie_bot.modules.greetings.handlers.status_overall import (
    WelcomeSettingsShowHandler,
)
from sophie_bot.modules.greetings.middlewares.leave_user import LeaveUserMiddleware
from sophie_bot.modules.greetings.middlewares.new_user import NewUserMiddleware
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Greetings")
__module_emoji__ = "🙋‍♂️"
__module_info__ = l_(
    "This module helps you to welcome new users automatically, while keeping the chat clean."
    "\nIf you want to enforce captcha / rules verification, please see 'Welcome Security' module instead."
)

router = Router(name="greetings")


__handlers__ = (
    EnableWelcomeHandlerABC,
    SetWelcomeMessageHandler,
    SetJoinRequestMessageHandler,
    DelJoinRequestMessageHandler,
    WelcomeSettingsShowHandler,
    CleanServiceHandlerABC,
    CleanWelcomeHandlerABC,
)


async def __pre_setup__():
    router.message.outer_middleware(LeaveUserMiddleware())
    router.message.outer_middleware(NewUserMiddleware())
