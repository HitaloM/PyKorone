import html
import re

from aiogram.types import Message, User

from sophie_bot.utils.i18n import gettext as _

RANDOM_REGEXP = re.compile(r"{([^{}]+)}")


def vars_parser(text: str, message: Message, user: User) -> str:
    if not text:
        return text

    # TODO: Remove html
    first_name = html.escape(user.first_name, quote=False)
    last_name = html.escape(user.last_name or "", quote=False)
    user_id = [user.id for user in message.new_chat_members][0] if message.new_chat_members else user.id

    if message.new_chat_members and message.new_chat_members[0].username:
        username = f"@{message.new_chat_members[0].username}"
    elif user.username:
        username = f"@{user.username}"
    else:
        username = user.first_name

    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or _("Local chat"), quote=False)

    return (
        text.replace("{first}", first_name)
        .replace("{last}", last_name)
        .replace("{fullname}", f"{first_name} {last_name}")
        .replace("{id}", str(user_id).replace("{userid}", str(user_id)))
        .replace("{username}", username)
        .replace("{chatid}", str(chat_id))
        .replace("{chatname}", str(chat_name))
        .replace("{chatnick}", str(message.chat.username or chat_name))
        .replace("{mention}", user.mention_html())
    )
