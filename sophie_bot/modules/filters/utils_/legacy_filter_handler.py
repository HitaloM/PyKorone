from random import choice
from string import printable

from aiogram.types import CallbackQuery, Message
from regex import regex
from stfu_tg import Code, Doc, Template
from stfu_tg.doc import Element

from sophie_bot.constants import AI_FILTER_LIMIT_PER_CHAT
from sophie_bot.db.models import FiltersModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.utils_.reply_or_edit import reply_or_edit
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


async def check_legacy_filter_handler(
    event: Message | CallbackQuery, keyword: str, connection: ChatConnection, editing_oid: str | None = None
) -> bool:
    if await FiltersModel.get_by_keyword(connection.tid, keyword):
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

        # Check AI filter limit per chat (only when adding a new AI filter)
        # When editing, we need to check if the existing filter was already an AI filter
        is_editing_ai_filter = False
        if editing_oid:
            from bson import ObjectId

            existing_filter = await FiltersModel.get_by_id(ObjectId(editing_oid))
            if existing_filter and existing_filter.handler.startswith("ai:"):
                is_editing_ai_filter = True

        # Only enforce limit if we're adding a new AI filter (not editing an existing one)
        if not is_editing_ai_filter:
            current_ai_filter_count = await FiltersModel.count_ai_filters(connection.tid)
            if current_ai_filter_count >= AI_FILTER_LIMIT_PER_CHAT:
                log.info(f"check_legacy_filter_handler: AI filter limit reached for chat {connection.tid}")
                return await reply_or_edit(
                    event,
                    Template(
                        _(
                            "Maximum number of AI filter handlers reached ({limit} per chat).\n"
                            "AI filters consume tokens and can overload the system. "
                            "Please remove an existing AI filter before adding a new one."
                        ),
                        limit=AI_FILTER_LIMIT_PER_CHAT,
                    ).to_html(),
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
