from __future__ import annotations

from typing import Any, Optional, Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from beanie import PydanticObjectId
from stfu_tg import KeyValue, Section

from sophie_bot.utils.i18n import gettext as _
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS

from .controller import WizardController
from .callbacks import ACWCoreCallback, ACWSettingCallback
from .helpers import _convert_action_data_to_model


class WizardRenderer:
    """Pure rendering utilities for Action Config Wizard screens.

    This class centralizes all UI construction for the Action Config Wizard.
    It returns text and reply markup for callers to display or edit messages.
    """

    @staticmethod
    async def render_home_page(
        handler: Any,
        *,
        chat_iid: PydanticObjectId,
        chat_title: str | None,
        state: FSMContext | None,
    ) -> Tuple[str, Any]:
        """Build home page text and keyboard.

        Returns (text_html, reply_markup)
        """
        model = await handler.get_model(chat_iid)
        actions = await handler.get_actions(model)

        items = [KeyValue(_("Chat"), chat_title or "Unknown")]
        builder = InlineKeyboardBuilder()

        if actions:
            for action in actions:
                action_meta = ALL_MODERN_ACTIONS.get(action.name)
                if not action_meta:
                    continue
                action_text = (
                    action_meta.description(_convert_action_data_to_model(action_meta, action.data))
                    if action_meta and action.data
                    else action.name
                )
                items.append(KeyValue(action_meta.title, action_text))
                builder.add(
                    InlineKeyboardButton(
                        text=f"{action_meta.icon} {action_meta.title}",
                        callback_data=ACWCoreCallback(
                            mod=handler.callback_prefix, op="configure", name=action.name
                        ).pack(),
                    )
                )

        # Add Save if staged changes exist
        has_changes = await WizardController.has_staged_changes(state, handler.module_name, chat_iid)
        if has_changes:
            builder.add(
                InlineKeyboardButton(
                    text=_("✅ Save"), callback_data=ACWCoreCallback(mod=handler.callback_prefix, op="done").pack()
                )
            )

        # Add add-new only if allowed or no actions yet
        allow_multiple = getattr(handler, "allow_multiple_actions", True)
        if allow_multiple or not actions:
            builder.add(
                InlineKeyboardButton(
                    text=_("➕ Add another action"),
                    callback_data=ACWCoreCallback(mod=handler.callback_prefix, op="add").pack(),
                )
            )
        builder.adjust(1)

        doc = Section(
            *items,
            title=_(getattr(handler, "wizard_title", "Action Configuration")),
        )

        return doc.to_html(), builder.as_markup()

    @staticmethod
    async def render_add_action_list(handler: Any, *, chat_tid: int) -> Tuple[str, Any]:
        """Build the 'select an action to add' page text and keyboard.

        Returns (text, reply_markup)
        """
        builder = InlineKeyboardBuilder()
        for action_name, action in ALL_MODERN_ACTIONS.items():
            button_text = f"{action.icon} {action.title}"
            callback_data = ACWCoreCallback(mod=handler.callback_prefix, op="select", name=action_name).pack()
            builder.add(InlineKeyboardButton(text=str(button_text), callback_data=callback_data))
        # Back button
        builder.adjust(2)
        builder.add(
            InlineKeyboardButton(
                text=_("🔙 Back"), callback_data=ACWCoreCallback(mod=handler.callback_prefix, op="back").pack()
            )
        )
        return _("Select an action to add:"), builder.as_markup()

    @staticmethod
    async def show_action_configured_message(
        event: CallbackQuery | Message,
        *,
        action_name: str,
        chat_tid: PydanticObjectId,
        callback_prefix: str,
        success_message: str,
        action_data: Optional[dict] = None,
        show_delete: bool = True,
        show_cancel: bool = True,
    ) -> None:
        """Render and send/edit the 'action configured' message with settings buttons.

        Side-effect: edits or replies to the event message.
        """
        action = ALL_MODERN_ACTIONS[action_name]

        # Convert action data to proper Pydantic model
        action_model = _convert_action_data_to_model(action, action_data)

        # Create confirmation message
        doc = Section(
            KeyValue(_("Action configured"), f"{action.icon} {action.title}"),
            KeyValue(_("Description"), action.description(action_model)),
            title=_("Action Configuration Complete"),
        )

        # Settings buttons
        settings = action.settings(action_model)
        builder = InlineKeyboardBuilder()
        if settings:
            for setting_id, setting in settings.items():
                button_text = f"{setting.icon} {setting.title}" if setting.icon else str(setting.title)
                cb_data = ACWSettingCallback(mod=callback_prefix, name=action_name, setting=setting_id).pack()
                builder.add(InlineKeyboardButton(text=button_text, callback_data=cb_data))
            builder.adjust(2)

        # Delete/back
        if show_delete:
            builder.row(
                InlineKeyboardButton(
                    text=_("🗑️ Delete this action"),
                    callback_data=ACWCoreCallback(mod=callback_prefix, op="remove", name=action_name).pack(),
                )
            )
        builder.row(
            InlineKeyboardButton(
                text=_("🔙 Back"), callback_data=ACWCoreCallback(mod=callback_prefix, op="back").pack()
            )
        )

        # Done/cancel
        done_button = InlineKeyboardButton(
            text=_("✅ Done"), callback_data=ACWCoreCallback(mod=callback_prefix, op="done").pack()
        )
        if show_cancel:
            cancel_button = InlineKeyboardButton(
                text=_("❌ Cancel"), callback_data=ACWCoreCallback(mod=callback_prefix, op="cancel").pack()
            )
            builder.row(cancel_button, done_button)
        else:
            builder.row(done_button)

        reply_markup = builder.as_markup()

        if isinstance(event, CallbackQuery):
            if event.message and isinstance(event.message, Message):
                await event.message.edit_text(str(doc), reply_markup=reply_markup)
            await event.answer(_(success_message) if success_message else _("Action configured successfully!"))
        else:
            await event.reply(str(doc), reply_markup=reply_markup)
