from types import ModuleType

from aiogram import Router
from stfu_tg import Doc

from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log

from .. import LOADED_MODULES
from .enforce_middleware import EnforceFiltersMiddleware
from .handlers.action_change_setting_confirm import ActionChangeSettingConfirm
from .handlers.action_remove import ActionRemoveHandler
from .handlers.action_select import ActionSelectHandler
from .handlers.action_setting_select import ActionSettingSelectHandler
from .handlers.action_setup_confirm import ActionSetupConfirmHandler
from .handlers.actions_list import ActionsListHandler
from .handlers.actions_list_to_remove import ActionsListToRemoveHandler
from .handlers.filter_confirm import FilterConfirmHandler
from .handlers.filter_del import FilterDeleteHandler
from .handlers.filter_edit import FilterEditHandler
from .handlers.filter_new import FilterNewHandler
from .handlers.filter_save import FilterSaveHandler
from .handlers.filters_list import FiltersListHandler
from .utils_.all_modern_actions import ALL_MODERN_ACTIONS
from .utils_.legacy_filter_actions import LEGACY_FILTERS_ACTIONS

router = Router(name="filters")
__module_name__ = l_("Filters")
__module_emoji__ = "🪄"
__module_info__ = LazyProxy(
    lambda: Doc(
        l_("Filters allows to invoke different actions for different messages."),
        l_("For example muting the users when they mention crypto."),
        l_(
            "Sophie supports many different actions you can configure to automatize chat moderation in many different ways."
        ),
    )
)
__advertise_wiki_page__ = True

__handlers__ = (
    FilterNewHandler,
    ActionsListHandler,
    ActionSetupConfirmHandler,
    ActionSelectHandler,
    FilterConfirmHandler,
    FilterSaveHandler,
    ActionSettingSelectHandler,
    FiltersListHandler,
    FilterDeleteHandler,
    ActionsListToRemoveHandler,
    ActionRemoveHandler,
    FilterEditHandler,
    ActionChangeSettingConfirm,
)


async def __pre_setup__():
    # Enforce filters middleware
    router.message.outer_middleware(EnforceFiltersMiddleware())
    router.edited_message.outer_middleware(EnforceFiltersMiddleware())


async def __post_setup__(modules: dict[str, ModuleType]):
    from ..notes.magic_handlers.reply_action import ReplyModernAction

    for name, module in modules.items():
        action_filters: tuple[type[ReplyModernAction], ...] = getattr(module, "__modern_actions__", tuple())

        for action_filter in action_filters:
            log.debug("Modern filter actions: Adding new action...", name=action_filter.name, module=name)

            ALL_MODERN_ACTIONS[action_filter.name] = action_filter()

    log.debug("Legacy filters: Filters actions", actions=LEGACY_FILTERS_ACTIONS)
