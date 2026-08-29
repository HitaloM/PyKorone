from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from magic_filter import F

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.help.callbacks import (
    HELP_MODULE_START_PREFIX,
    HELP_START_PAYLOAD,
    PMHelpModule,
    PMHelpModules,
    parse_help_module_start_payload,
)
from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.modules.help.utils.menu import build_rich_help_menu
from korone.modules.help.utils.presentation import build_module_back_button, build_module_help
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.telegram_errors import is_callback_query_expired_error

if TYPE_CHECKING:
    from aiogram import Router
    from aiogram.dispatcher.event.handler import CallbackType


class PMModulesList(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(
            cls,
            CommandStart(deep_link=True, magic=F.args == HELP_START_PAYLOAD),
            PrivateChatFilter(),
            flags={"help": {"exclude": True}},
        )
        router.callback_query.register(cls, PMHelpModules.filter())

    async def handle(self) -> None:
        callback_data = self.callback_data
        if not isinstance(callback_data, PMHelpModules):
            callback_data = None
        if isinstance(self.event, CallbackQuery):
            try:
                await self.event.answer()
            except TelegramBadRequest as error:
                if not is_callback_query_expired_error(error):
                    raise

        rich_message, reply_markup = build_rich_help_menu(callback_data)
        await self.answer_rich(rich_message, reply_markup=reply_markup)


@flags.help(exclude=True)
class PMModuleStartHelp(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return CommandStart(deep_link=True, magic=F.args.startswith(HELP_MODULE_START_PREFIX)), PrivateChatFilter()

    async def handle(self) -> None:
        payload = self.command.args if self.command is not None else None
        module_name = parse_help_module_start_payload(payload) if payload is not None else None
        if module_name is None or (module := HELP_MODULES.get(module_name)) is None or module.exclude_public:
            await self.answer(_("Module not found."), reply_markup=build_module_back_button())
            return

        rich_message = build_module_help(module_name, module)
        await self.event.answer_rich(rich_message, reply_markup=build_module_back_button())


class PMModuleHelp(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (PMHelpModule.filter(),)

    async def handle(self) -> None:
        callback_data = cast("PMHelpModule", self.callback_data)
        module_name = callback_data.module_name
        module = HELP_MODULES.get(module_name)

        if not module:
            await self.event.answer(_("Module not found."))
            return

        rich_message = build_module_help(module_name, module)
        reply_markup = build_module_back_button(back_to_start=callback_data.back_to_start)

        await self.check_for_message()
        await self.edit_rich(rich_message, reply_markup=reply_markup)
        await self.event.answer()
