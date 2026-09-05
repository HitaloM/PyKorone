from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from aiogram.exceptions import TelegramBadRequest

from korone.args import ArgumentSchema, BooleanArg
from korone.ui import Italic, MessageContent, Renderable, field, section, template
from korone.ui.rendering import text_kwargs
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_
from korone.utils.telegram_errors import is_topic_closed_error

if TYPE_CHECKING:
    from collections.abc import Mapping

    from korone.utils.i18n import LazyProxy


@dataclass(frozen=True, slots=True)
class StatusArguments:
    new_status: bool | None = None


class BooleanStatusHandler(KoroneMessageHandler[StatusArguments]):
    header_text: LazyProxy
    status_texts: ClassVar[Mapping[bool, LazyProxy]] = {True: l_("Enabled"), False: l_("Disabled")}
    change_command: str | None = None
    change_args: str = "on / off"

    arguments = ArgumentSchema(StatusArguments, new_status=BooleanArg(l_("New status")))

    @abstractmethod
    async def get_status(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def set_status(self, *, new_status: bool) -> None:
        raise NotImplementedError

    def status_text(self, *, status_data: bool) -> Renderable:
        return self.status_texts[status_data]

    async def reply_status(self, text: MessageContent) -> None:
        try:
            await self.answer(text)
        except TelegramBadRequest as error:
            if not is_topic_closed_error(error):
                raise
            await self.bot.send_message(chat_id=self.event.chat.id, **text_kwargs(text))

    async def display_current_status(self) -> None:
        status_data: bool = await self.get_status()

        extra = (
            template(_("Use '{cmd}' to change it."), cmd=Italic(f"/{self.change_command} <{self.change_args}>"))
            if self.change_command
            else None
        )
        doc = section(
            self.header_text,
            field(_("Current state"), self.status_text(status_data=status_data)),
            field(_("Chat"), self.chat.title),
            extra,
        )
        await self.reply_status(doc)

    async def change_status(self, *, new_status: bool) -> None:
        current_status: bool = await self.get_status()

        if current_status == new_status:
            await self.reply_status(
                template(
                    _("The current status is already {state}"),
                    state=Italic(self.status_text(status_data=current_status)),
                )
            )
            return

        await self.set_status(new_status=new_status)

        doc = section(
            self.header_text,
            _("The state was successfully changed"),
            field(_("New state"), self.status_text(status_data=new_status)),
            field(_("Chat"), self.chat.title),
        )
        await self.reply_status(doc)

    async def handle(self) -> None:
        new_status = self.args.new_status

        if new_status is None:
            return await self.display_current_status()

        return await self.change_status(new_status=new_status)
