from __future__ import annotations

from typing import Optional

from aiogram.types import User, Chat

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnModel, WarnSettingsModel
from sophie_bot.modules.restrictions.utils.restrictions import ban_user, kick_user, mute_user
from sophie_bot.utils.i18n import gettext as _


async def warn_user(
    chat: Chat, user: User, admin: User, reason: Optional[str] = None
) -> tuple[int, int, Optional[str]]:
    """
    Warns a user in a chat.
    Returns: (current_warns, max_warns, punishment_action_if_any)
    """
    # Get database models
    chat_model = await ChatModel.get_by_tid(chat.id)
    if not chat_model:
        # Should normally exist if this is called from a handler
        chat_model = await ChatModel.create_new(chat.id)

    settings = await WarnSettingsModel.get_or_create(chat_model.iid)

    # Create warn record
    warn = WarnModel(chat=chat_model.iid, user_id=user.id, admin_id=admin.id, reason=reason)
    await warn.save()

    # Check counts
    current_warns = await WarnModel.count_user_warns(chat_model.iid, user.id)
    max_warns = settings.max_warns

    punishment = None

    if current_warns >= max_warns:
        # Reset warns
        await WarnModel.find(WarnModel.chat.id == chat_model.iid, WarnModel.user_id == user.id).delete()  # type: ignore[unresolved-attribute]

        # Execute punishment
        # Default is ban if no actions defined
        if not settings.actions:
            if await ban_user(chat.id, user.id):
                punishment = _("banned")
        else:
            # We execute the first defined action for now, as typical warn systems usually have one escalation
            # But the model supports a list. We'll iterate but typically it's one outcome.
            for action in settings.actions:
                if action.name == "ban_user":
                    if await ban_user(chat.id, user.id):
                        punishment = _("banned")
                elif action.name == "kick_user":
                    if await kick_user(chat.id, user.id):
                        punishment = _("kicked")
                elif action.name == "mute_user":
                    if await mute_user(chat.id, user.id):
                        punishment = _("muted")
                elif action.name == "tmute_user":
                    # data should contain time
                    # time_val = action.data.get("time")
                    # Logic to parse time would be needed here if not pre-parsed
                    # Assuming basic mute for now if complex time logic is needed
                    if await mute_user(chat.id, user.id):
                        punishment = _("muted")

                # If we successfully punished, break (usually only one punishment applies)
                if punishment:
                    break

    return current_warns, max_warns, punishment
