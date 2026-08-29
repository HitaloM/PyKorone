from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import TextArg, define_arguments
from korone.modules.web.utils.misc import normalize_url
from korone.ui import Code, field, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Normalize a URL."))
@flags.disableable(name="url")
class URLNormalizeHandler(KoroneMessageHandler):
    arguments = define_arguments(url=TextArg(l_("URL")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("url"),)

    async def handle(self) -> None:
        raw_url = (self.data.get("url") or "").strip()

        if not raw_url:
            await self.answer(
                template(
                    _("You should provide a URL. Example: {example}."),
                    example=Code("/url example.com/path?utm_source=test#section"),
                )
            )
            return

        normalized = normalize_url(raw_url)
        if not normalized:
            await self.answer(template(_("I couldn't normalize this URL: {url}"), url=Code(raw_url)))
            return

        if normalized == raw_url:
            await self.answer(template(_("This URL is already normalized: {url}"), url=Code(raw_url)))
            return

        await self.answer(
            section(_("URL Normalization"), field(_("Input"), Code(raw_url)), field(_("Normalized"), Code(normalized)))
        )
