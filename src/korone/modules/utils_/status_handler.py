from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Never, TypeVar

from ass_tg.types import BooleanArg, OptionalArg
from stfu_tg import Italic, KeyValue, Section, Template

from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric
    from stfu_tg.doc import Element

    from korone.utils.handlers import HandlerData
    from korone.utils.i18n import LazyProxy

T = TypeVar("T")


class StatusHandlerABC[T](KoroneMessageHandler):
    header_text: LazyProxy
    status_texts: dict[T, LazyProxy]
    change_command: str | None = None
    change_args: str | LazyProxy = "on / off"

    @classmethod
    async def handler_args(cls, message: Message | None, data: HandlerData) -> dict[str, ArgFabric]:
        return {"new_status": OptionalArg(BooleanArg(l_("?New status")))}

    @abstractmethod
    async def get_status(self) -> T:
        raise NotImplementedError

    @abstractmethod
    async def set_status(self, new_status: T) -> Never:
        raise NotImplementedError

    def status_text(self, status_data: T) -> Element | str | LazyProxy:
        return self.status_texts[status_data]

    async def display_current_status(self) -> None:
        status_data: T = await self.get_status()

        doc = Section(
            KeyValue("Current state", self.status_text(status_data)),
            KeyValue(_("Chat"), self.chat.title),
            title=self.header_text,
        )
        if self.change_command:
            doc += Template(_("Use '{cmd}' to change it."), cmd=Italic(f"/{self.change_command} <{self.change_args}>"))

        await self.event.reply(str(doc))

    async def change_status(self, new_status: T) -> None:
        current_status: T = await self.get_status()

        if current_status == new_status:
            await self.event.reply(
                str(
                    Template(_("The current status is already {state}"), state=Italic(self.status_text(current_status)))
                )
            )
            return

        await self.set_status(new_status)

        doc = Section(
            _("The state was successfully changed"),
            KeyValue("New state", self.status_text(new_status)),
            KeyValue(_("Chat"), self.chat.title),
            title=self.header_text,
        )
        await self.event.reply(str(doc))

    async def handle(self) -> None:
        new_status: bool | None = self.data.get("new_status", None)

        if new_status is None:
            return await self.display_current_status()

        return await self.change_status(new_status)


class StatusBoolHandlerABC(StatusHandlerABC[bool], ABC):
    status_texts: ClassVar[dict[bool, LazyProxy]] = {True: l_("Enabled"), False: l_("Disabled")}
