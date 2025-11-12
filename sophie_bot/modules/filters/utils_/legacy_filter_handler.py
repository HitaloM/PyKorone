from random import choice
from string import printable

from aiogram.types import CallbackQuery, Message
from regex import regex
from stfu_tg import Code, Doc, Template
from stfu_tg.doc import Element

from sophie_bot.db.models import FiltersModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.utils_.reply_or_edit import reply_or_edit
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


async def check_legacy_filter_handler(event: Message | CallbackQuery, keyword: str, connection: ChatConnection) -> bool:
    if await FiltersModel.get_by_keyword(connection.id, keyword):
        return await reply_or_edit(
            event,
            Doc(
                Template(
                    _("Filter with the handler {handler} already exists!"),
                    handler=Code(keyword),
                ),
                Template(_("You can edit the filter's actions with {cmd}."), cmd=Code(f"/editfilter {keyword}")),
            ).to_html(),
        )

    if keyword.startswith("ai:"):
        prompt = keyword[3:].strip()
        if not prompt:
            log.info("check_legacy_filter_handler: empty AI prompt")
            return await reply_or_edit(
                event,
                _(
                    "AI filter prompt cannot be empty. Please provide a description of when to trigger the filter.\n"
                    "Example: ai:Message contains crypto scam"
                ),
            )

    if keyword.startswith("re:"):
        pattern = keyword[3:]
        random_text_str = "".join(choice(printable) for _q in range(50))
        try:
            regex.match(pattern, random_text_str, timeout=0.2)
        except TimeoutError:
            log.info("check_legacy_filter_handler: regex too slow")
            return await reply_or_edit(
                event,
                _(
                    "Provided regex pattern is too slow to execute. Please review the pattern and try adding the filter again."
                ),
            )


def text_legacy_handler_handles_on(keyword: str) -> Element:
    if keyword.startswith("ai:"):
        return Template(_("When AI detects: {prompt}"), prompt=Code(keyword[3:]))

    if keyword.startswith("re:"):
        return Template(_("When messages matches the regex pattern {pattern}"), pattern=Code(keyword[3:]))

    return Template(_("When {handler} in message"), handler=Code(keyword))
