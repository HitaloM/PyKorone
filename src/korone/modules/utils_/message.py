from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message


def is_real_reply(message: Message) -> bool:

    if not message.reply_to_message:
        return False

    return not message.reply_to_message.forum_topic_created
