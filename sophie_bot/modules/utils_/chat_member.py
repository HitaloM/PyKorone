from aiogram.types import ResultChatMemberUnion

from sophie_bot.db.models import ChatAdminModel, ChatModel
from sophie_bot.services.bot import bot
from sophie_bot.utils.logger import log


async def save_chat_member(chat_iid, user_iid, member: ResultChatMemberUnion):
    log.debug("user_details: updating chat member", member_id=member.user.id)
    await ChatAdminModel.upsert_admin(chat_iid, user_iid, member)


async def get_chat_members(chat_tid: int) -> list[ResultChatMemberUnion]:
    return await bot.get_chat_administrators(chat_tid)


async def update_chat_members(chat: ChatModel):
    chat_members = await get_chat_members(chat.chat_id)
    for member in chat_members:
        user = await ChatModel.get_by_tid(member.user.id)
        if not user:
            log.debug("user_details: user not found in database", user_id=member.user.id)
            continue

        await save_chat_member(chat.id, user.id, member)
