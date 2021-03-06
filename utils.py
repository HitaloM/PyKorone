# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import spamwatch
import asyncpraw
from config import SW_API, REDDIT_SECRET, REDDIT_ID

REDDIT = asyncpraw.Reddit(
    client_id=REDDIT_ID, client_secret=REDDIT_SECRET, user_agent="PyKorone"
)

# SpamWatch
spamwatch_api = SW_API

if spamwatch_api == "None":
    sw = None
else:
    try:
        sw = spamwatch.Client(spamwatch_api)
    except BaseException:
        sw = None


def pretty_size(size):
    units = ["B", "KB", "MB", "GB"]
    unit = 0
    while size >= 1024:
        size /= 1024
        unit += 1
    return "%0.2f %s" % (size, units[unit])
