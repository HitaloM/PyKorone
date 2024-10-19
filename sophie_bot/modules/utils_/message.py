from aiogram.types import Message


def is_real_reply(message: Message):
    """Returns True if the message has a real reply"""

    if not message.reply_to_message:
        return False

    if message.reply_to_message.forum_topic_created:
        return False

    return True
