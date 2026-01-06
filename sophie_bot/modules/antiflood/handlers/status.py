from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Italic, KeyValue, Section, Template

from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.antiflood import FLOOD_WINDOW_SECONDS
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.utils_.action_config_wizard.helpers import _convert_action_data_to_model
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Show antiflood settings"))
@flags.disableable(name="antiflood")
class AntifloodStatusHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("antiflood"), UserRestricting(admin=True)

    async def handle(self) -> Any:
        model = await AntifloodModel.get_by_chat_iid(self.connection.db_model.iid)

        """Display current antiflood status."""
        status_text = _("Enabled") if model.enabled else _("Disabled")

        items: list[KeyValue] = [
            KeyValue(_("Status"), status_text),
            KeyValue(
                _("Message threshold"),
                Template(
                    _("{message_count} messages in {seconds} seconds"),
                    message_count=model.message_count,
                    seconds=FLOOD_WINDOW_SECONDS,
                ),
            ),
        ]

        # Render actions (modern, multiple)
        for action in model.actions:
            meta = ALL_MODERN_ACTIONS.get(action.name)
            if not meta:
                continue
            action_model = _convert_action_data_to_model(meta, action.data)
            action_text = meta.description(action_model) if action_model else meta.title
            items.append(KeyValue(meta.title, action_text))

        items.append(KeyValue(_("Chat"), self.connection.title))

        doc = Section(
            *items,
            title=_("Antiflood Protection"),
        )

        doc += Template(
            _("Use '{enable_cmd}' to enable/disable or '{action_cmd}' to configure actions."),
            enable_cmd=Italic("/setflood <off / count>"),
            action_cmd=Italic("/setfloodaction"),
        )

        await self.event.reply(str(doc))
