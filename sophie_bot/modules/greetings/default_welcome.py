from stfu_tg import Doc, Section

from sophie_bot.db.models.notes import Saveable
from sophie_bot.utils.i18n import gettext as _


def get_default_welcome_message(has_rules: bool) -> Saveable:
    doc = Doc(
        _("Hi {mention}! Welcome in the group."),
        Section("{rules}", title=_("Group rules")) if has_rules else _("There are no rules in this group, have fun!"),
    )
    return Saveable(text=str(doc))


def get_default_security_message() -> Saveable:
    doc = Doc(
        _("Hi {mention}! Welcome to the {chatname}!"),
        _("⬇️ Please click the button below to participate in the group."),
        "[I am not a bot!](btnwelcomesecurity)️",
    )
    return Saveable(text=str(doc))


def get_default_join_request_message() -> Saveable:
    doc = Doc(
        _("Hi {mention}!"),
        _("Please check your direct messages with me to complete verification and join the group."),
    )
    return Saveable(text=str(doc))
