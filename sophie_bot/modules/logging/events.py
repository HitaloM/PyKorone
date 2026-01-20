from enum import Enum
from sophie_bot.utils.i18n import lazy_gettext as l_


class LogEvent(str, Enum):
    # Warnings
    WARN_ADDED = "warn_added"
    WARN_REMOVED = "warn_removed"
    WARN_RESET = "warn_reset"
    ALL_WARNS_RESET = "all_warns_reset"

    # Notes
    NOTE_SAVED = "note_saved"
    NOTE_DELETED = "note_deleted"
    NOTE_UPDATED = "note_updated"
    ALL_NOTES_DELETED = "all_notes_deleted"

    # Restrictions
    USER_RESTRICTED = "user_restricted"
    USER_UNRESTRICTED = "user_unrestricted"
    USER_BANNED = "user_banned"
    USER_UNBANNED = "user_unbanned"
    USER_KICKED = "user_kicked"
    USER_MUTED = "user_muted"
    USER_UNMUTED = "user_unmuted"

    # Filters
    FILTER_SAVED = "filter_saved"
    FILTER_DELETED = "filter_deleted"

    # Purges
    MESSAGES_PURGED = "messages_purged"
    MESSAGE_DELETED = "message_deleted"


LOG_EVENT_STRINGS = {
    LogEvent.WARN_ADDED: l_("Warning added"),
    LogEvent.WARN_REMOVED: l_("Warning removed"),
    LogEvent.WARN_RESET: l_("Warning reset"),
    LogEvent.ALL_WARNS_RESET: l_("All warnings reset"),
    LogEvent.NOTE_SAVED: l_("Note saved"),
    LogEvent.NOTE_DELETED: l_("Note deleted"),
    LogEvent.NOTE_UPDATED: l_("Note updated"),
    LogEvent.ALL_NOTES_DELETED: l_("All notes deleted"),
    LogEvent.USER_RESTRICTED: l_("User restricted"),
    LogEvent.USER_UNRESTRICTED: l_("User unrestricted"),
    LogEvent.USER_BANNED: l_("User banned"),
    LogEvent.USER_UNBANNED: l_("User unbanned"),
    LogEvent.USER_KICKED: l_("User kicked"),
    LogEvent.USER_MUTED: l_("User muted"),
    LogEvent.USER_UNMUTED: l_("User unmuted"),
    LogEvent.FILTER_SAVED: l_("Filter saved"),
    LogEvent.FILTER_DELETED: l_("Filter deleted"),
    LogEvent.MESSAGES_PURGED: l_("Messages purged"),
    LogEvent.MESSAGE_DELETED: l_("Message deleted"),
}
