import asyncio
from typing import Sequence

from sophie_bot.db.models import ChatModel, WSUserModel
from sophie_bot.modules.legacy_modules.utils.restrictions import mute_user
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin


async def ws_on_new_user(new_user: ChatModel, chat: ChatModel, is_join_request: bool = False):
    """
    Function initializes welcomesecurity process internally.
    Returns whenever the user was muted.
    """

    # Check for admin permissions
    if await is_user_admin(chat_id=chat.chat_id, user_id=new_user.chat_id):
        return False

    # Add user to the welcomesecurity database
    ws_user_db = await WSUserModel.ensure_user(new_user, chat, is_join_request)
    if ws_user_db.passed:
        # The user already passed the verification in this chat - skipping
        return False

    return True


async def ws_on_new_user_mute(new_user: ChatModel, chat: ChatModel):
    if await ws_on_new_user(new_user, chat):
        return await mute_user(chat_id=chat.chat_id, user_id=new_user.chat_id)
    return None


async def ws_on_new_users_mute(new_users: Sequence[ChatModel], chat: ChatModel) -> list[bool]:
    return await asyncio.gather(*(ws_on_new_user_mute(new_user, chat) for new_user in new_users))
