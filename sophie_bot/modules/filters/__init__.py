from types import ModuleType

from aiogram import Router

from sophie_bot.modules.filters.enforce_middleware import EnforceFiltersMiddleware
from sophie_bot.utils.i18n import lazy_gettext as l_

from .utils_.filter_abc import ALL_FILTER_ACTIONS

__module_name__ = l_("Filters")
__module_emoji__ = "🪄"

from ...utils.logger import log
from ..notes.magic_handlers.modern_filter import ReplyFilterAction

router = Router(name="filters")

__handlers__ = ()  # (AddFilterHandler, FilterActionClickHandler, FilterActionConfirmHandler)


async def __pre_setup__():
    # Enforce filters middleware
    router.message.outer_middleware(EnforceFiltersMiddleware())
    router.edited_message.outer_middleware(EnforceFiltersMiddleware())


async def __post_setup__(modules: dict[str, ModuleType]):
    for name, module in modules.items():
        action_filters: tuple[ReplyFilterAction, ...] = getattr(module, "__modern_filters__", tuple())

        for action_filter in action_filters:
            log.debug("Modern filter actions: Adding new action...", name=action_filter.name, module=name)

            ALL_FILTER_ACTIONS[action_filter.name] = action_filter

            # if action_filter.additional_handlers:
            #     log.debug("- action has additional handlers, adding to the filters router...")
            #     for handler in action_filter.additional_handlers:
            #         handler.register(router)
