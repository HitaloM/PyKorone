from sophie_bot.db.models import ChatModel, WSUserModel
from sophie_bot.db.models.greetings import WelcomeMute
from sophie_bot.modules.restrictions.utils.restrictions import unmute_user
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.welcomesecurity.utils_.db_time_convert import (
    convert_timedelta_or_str,
)
from sophie_bot.modules.welcomesecurity.utils_.welcomemute import on_welcomemute


async def ws_on_user_passed(user: ChatModel, group: ChatModel, welcomemute: WelcomeMute) -> bool:
    """
    Function when user successfully passed the welcomesecurity
    Returns whenever the user was unmuted.
    """

    # Check for admin permissions
    if await is_user_admin(chat=group.tid, user=user.tid):
        return False

    # Remove the user from the welcomesecurity database
    await WSUserModel.remove_user(user.iid, group.iid)

    # Unmute / restrict user
    if welcomemute.enabled and welcomemute.time:
        await on_welcomemute(group.tid, user.tid, on_time=convert_timedelta_or_str(welcomemute.time))
    else:
        await unmute_user(chat_tid=group.tid, user_tid=user.tid)

    return True
