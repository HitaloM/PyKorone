from aiogram.types import CallbackQuery, Message

from korone.utils.exception import KoroneError


def get_message(event: Message | CallbackQuery) -> Message:
    message = event if isinstance(event, Message) else event.message
    if not isinstance(message, Message):
        raise KoroneError.inaccessible_message()
    return message


def is_real_reply(message: Message) -> bool:

    if not message.reply_to_message:
        return False

    return not message.reply_to_message.forum_topic_created
