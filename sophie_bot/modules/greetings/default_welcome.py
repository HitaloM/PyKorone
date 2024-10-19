from stfu_tg import Doc, Section

from sophie_bot.db.models.notes import Saveable
from sophie_bot.utils.i18n import gettext as _


def get_default_welcome_message(has_rules: bool) -> Saveable:
    doc = Doc(
        _("Hi {mentions}! Welcome in the group."),
        Section("{rules}", title=_("Group rules")) if has_rules else _("There are no rules in this group, have fun!"),
    )
    return Saveable(text=str(doc))


def get_default_security_message() -> Saveable:
    return Saveable(
        text=_(
            (
                "Hi {mentions}! Welcome to the {chatname}!"
                "\n⬇️Please click the button below to participate in the group."
                "[I am not a bot!](btnwelcomesecurity)️"
            )
        )
    )
