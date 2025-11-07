from aiogram import Router

from sophie_bot.modules.federations.handlers.accept_transfer import AcceptTransferHandler
from sophie_bot.modules.federations.handlers.ban import FederationBanHandler
from sophie_bot.modules.federations.handlers.banlist import FederationBanListHandler
from sophie_bot.modules.federations.handlers.create import CreateFederationHandler
from sophie_bot.modules.federations.handlers.info import FederationInfoHandler
from sophie_bot.modules.federations.handlers.join import JoinFederationHandler
from sophie_bot.modules.federations.handlers.leave import LeaveFederationHandler
from sophie_bot.modules.federations.handlers.logs import SetFederationLogHandler, UnsetFederationLogHandler
from sophie_bot.modules.federations.handlers.subscribe import SubscribeFederationHandler, UnsubscribeFederationHandler
from sophie_bot.modules.federations.handlers.transfer import TransferOwnershipHandler
from sophie_bot.modules.federations.handlers.unban import FederationUnbanHandler
from sophie_bot.modules.federations.middlewares.check_fban import FedBanMiddleware
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Federations (new)")
__module_emoji__ = "🏛"
__module_info__ = l_(
    "Federations allow you to manage multiple chats as a group. "
    "You can ban users across all chats in a federation, "
    "subscribe to other federations, and manage permissions."
)

router = Router(name="federations")

__handlers__ = (
    CreateFederationHandler,
    JoinFederationHandler,
    LeaveFederationHandler,
    FederationInfoHandler,
    FederationBanHandler,
    FederationUnbanHandler,
    FederationBanListHandler,
    TransferOwnershipHandler,
    AcceptTransferHandler,
    SetFederationLogHandler,
    UnsetFederationLogHandler,
    SubscribeFederationHandler,
    UnsubscribeFederationHandler,
)


async def __pre_setup__():
    router.message.outer_middleware(FedBanMiddleware())
