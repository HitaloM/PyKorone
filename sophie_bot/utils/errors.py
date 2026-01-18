# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Common error messages for Sophie Bot.

This module provides standardized error message functions to ensure
consistency across the codebase and reduce duplication.
"""

from stfu_tg import Code, Template

from sophie_bot.utils.i18n import gettext as _


# =============================================================================
# Command/Handler Errors
# =============================================================================


def command_not_found(cmd_name: str) -> str:
    """Return error message for command not found."""
    return str(Template(_("Command {cmd} not found."), cmd=Code("/" + cmd_name)))


# =============================================================================
# Setup/Wizard Errors
# =============================================================================


def setup_data_not_found() -> str:
    """Return error message for missing setup data."""
    return _("Setup data not found. Please try again.")


def setup_session_expired() -> str:
    """Return error message for expired setup session."""
    return _("Setup session expired. Please start again.")


def invalid_chat_context() -> str:
    """Return error message for invalid chat context."""
    return _("Invalid chat context. Please restart the setup.")


def invalid_action() -> str:
    """Return error message for invalid action."""
    return _("Invalid action.")


def invalid_action_configuration() -> str:
    """Return error message for invalid action configuration."""
    return _("Invalid action configuration.")


def invalid_setting() -> str:
    """Return error message for invalid setting."""
    return _("Invalid setting.")


def setting_not_available() -> str:
    """Return error message for unavailable setting configuration."""
    return _("Setting configuration not available.")


# =============================================================================
# Resource Errors
# =============================================================================


def chat_not_found() -> str:
    """Return error message for chat not found."""
    return _("Chat not found.")


def note_not_found(note_name: str) -> str:
    """Return error message for note not found."""
    from stfu_tg import Bold

    return _("#{name} note was not found.").format(name=Bold(note_name))


# =============================================================================
# Duration/Input Errors
# =============================================================================


def invalid_duration(action_type: str) -> str:
    """Return error message for invalid duration.

    Args:
        action_type: Type of action (e.g., "ban", "mute")
    """
    return _("Invalid {action} duration, please try again.").format(action=action_type)
