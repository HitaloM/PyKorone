from aiogram.types import Message


def is_real_reply(message: Message):

    if not message.reply_to_message:
        return False

    if message.reply_to_message.forum_topic_created:
        return False

    return True
