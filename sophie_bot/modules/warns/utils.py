from __future__ import annotations

from typing import Optional

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnModel, WarnSettingsModel
from sophie_bot.modules.restrictions.utils.restrictions import ban_user, kick_user, mute_user
from sophie_bot.utils.i18n import gettext as _


async def warn_user(
    chat: ChatModel, user: ChatModel, admin: ChatModel, reason: Optional[str] = None
) -> tuple[int, int, Optional[str]]:
    """
    Warns a user in a chat.
    Returns: (current_warns, max_warns, punishment_action_if_any)
    """
    settings = await WarnSettingsModel.get_or_create(chat.iid)

    # Create warn record
    warn = WarnModel(chat=chat.iid, user_id=user.tid, admin_id=admin.tid, reason=reason)
    await warn.save()

    # Check counts
    current_warns = await WarnModel.count_user_warns(chat.iid, user.tid)
    max_warns = settings.max_warns

    punishment = None

    if current_warns >= max_warns:
        # Reset warns
        await WarnModel.find(WarnModel.chat.iid == chat.iid, WarnModel.user_id == user.tid).delete()  # type: ignore

        # Execute punishment
        # Default is ban if no actions defined
        if not settings.actions:
            if await ban_user(chat.tid, user.tid):
                punishment = _("banned")
        else:
            # We execute the first defined action for now, as typical warn systems usually have one escalation
            # But the model supports a list. We'll iterate but typically it's one outcome.
            for action in settings.actions:
                if action.name == "ban_user":
                    if await ban_user(chat.tid, user.tid):
                        punishment = _("banned")
                elif action.name == "kick_user":
                    if await kick_user(chat.tid, user.tid):
                        punishment = _("kicked")
                elif action.name == "mute_user":
                    if await mute_user(chat.tid, user.tid):
                        punishment = _("muted")
                elif action.name == "tmute_user":
                    # data should contain time
                    # time_val = action.data.get("time")
                    # Logic to parse time would be needed here if not pre-parsed
                    # Assuming basic mute for now if complex time logic is needed
                    if await mute_user(chat.tid, user.tid):
                        punishment = _("muted")

                # If we successfully punished, break (usually only one punishment applies)
                if punishment:
                    break

    return current_warns, max_warns, punishment
