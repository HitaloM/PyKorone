from types import ModuleType

from aiogram import Router
from stfu_tg import Doc

from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log

from .. import LOADED_MODULES
from ..legacy_modules import LOADED_LEGACY_MODULES
from .enforce_middleware import EnforceFiltersMiddleware
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
    FilterConfirmHandler,
    FilterSaveHandler,
    FiltersListHandler,
    FilterDeleteHandler,
    FilterEditHandler,
)


async def __pre_setup__():
    # Enforce filters middleware
    router.message.outer_middleware(EnforceFiltersMiddleware())
    router.edited_message.outer_middleware(EnforceFiltersMiddleware())

    # Register standardized Action Config Wizard for Filters
    from aiogram.fsm.context import FSMContext

    from sophie_bot.db.models.filters import FilterActionType, FilterInSetupType
    from sophie_bot.filters.admin_rights import UserRestricting
    from sophie_bot.filters.cmd import CMDFilter
    from sophie_bot.modules.utils_.action_config_wizard.factory import (
        register_action_config_system,
    )

    async def get_filter_model(self, chat_tid: int) -> FilterInSetupType:
        state: FSMContext | None = self.data.get("state")
        if not isinstance(state, FSMContext):
            raise ValueError("State not available for filter configuration")
        return await FilterInSetupType.get_filter(state, data=self.data)

    async def get_filter_actions(self, model: FilterInSetupType) -> list[FilterActionType]:
        return [FilterActionType(name=k, data=v) for k, v in model.actions.items()]

    async def add_filter_action(self, chat_tid: int, action_name: str, action_data: dict | None = None) -> None:
        state: FSMContext | None = self.data.get("state")
        if not isinstance(state, FSMContext):
            raise ValueError("State not available for filter configuration")
        filter_item = await FilterInSetupType.get_filter(state, data=self.data)
        # Enforce single action per filter: overwrite
        filter_item.actions = {action_name: action_data or {}}
        await filter_item.set_filter_state(state)

    async def remove_filter_action(self, chat_tid: int, action_id: str) -> None:
        state: FSMContext | None = self.data.get("state")
        if not isinstance(state, FSMContext):
            raise ValueError("State not available for filter configuration")
        filter_item = await FilterInSetupType.get_filter(state, data=self.data)
        if action_id in filter_item.actions:
            del filter_item.actions[action_id]
        await filter_item.set_filter_state(state)

    register_action_config_system(
        router,
        module_name="filters",
        callback_prefix="filter_action",
        wizard_title="Filter Action Configuration",
        success_message="Filter action updated successfully!",
        get_model_func=get_filter_model,
        get_actions_func=get_filter_actions,
        add_action_func=add_filter_action,
        remove_action_func=remove_filter_action,
        command_filter=CMDFilter("__filters_action_config"),  # command entry not used; callbacks drive the UI
        admin_filter=UserRestricting(admin=True),
        allow_multiple_actions=False,
    )


async def __post_setup__(modules: dict[str, ModuleType]):
    from ..notes.magic_handlers.reply_action import ReplyModernAction

    for name, module in modules.items():
        action_filters: tuple[type[ReplyModernAction], ...] = getattr(module, "__modern_actions__", tuple())

        for action_filter in action_filters:
            log.debug("Modern filter actions: Adding new action...", name=action_filter.name, module=name)

            ALL_MODERN_ACTIONS[action_filter.name] = action_filter()

    # Legacy filters
    log.debug("Legacy filters: Adding filters actions")
    for module in (*LOADED_LEGACY_MODULES, *LOADED_MODULES.values()):
        if not getattr(module, "__filters__", None):
            continue

        module_name = module.__name__.split(".")[-1]
        log.debug(f"Legacy filters: Adding filter action from {module_name} module")
        for data in module.__filters__.items():
            LEGACY_FILTERS_ACTIONS[data[0]] = data[1]

    log.debug("Legacy filters: Filters actions", actions=LEGACY_FILTERS_ACTIONS)
