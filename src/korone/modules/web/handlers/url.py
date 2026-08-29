from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import ArgumentSchema
from korone.modules.web.args import NormalizedURL, URLArg
from korone.ui import Code, field, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@dataclass(frozen=True, slots=True)
class URLNormalizeArguments:
    url: NormalizedURL


@flags.help(description=l_("Normalize a URL."))
@flags.disableable(name="url")
class URLNormalizeHandler(KoroneMessageHandler[URLNormalizeArguments]):
    arguments = ArgumentSchema(URLNormalizeArguments, url=URLArg(l_("URL")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("url"),)

    async def handle(self) -> None:
        url = self.args.url

        if url.normalized == url.original:
            await self.answer(template(_("This URL is already normalized: {url}"), url=Code(url.original)))
            return

        await self.answer(
            section(
                _("URL Normalization"),
                field(_("Input"), Code(url.original)),
                field(_("Normalized"), Code(url.normalized)),
            )
        )
