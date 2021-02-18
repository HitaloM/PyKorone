# This file is part of Korone (Telegram Bot)

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
from httpx import AsyncClient
from google_trans_new import google_translator
from config import SW_API, REDITT_SECRET, REDDIT_ID

translator = google_translator()

http = AsyncClient(http2=True)

REDDIT = asyncpraw.Reddit(
    client_id=REDITT_SECRET, client_secret=REDITT_SECRET, user_agent="PyKorone"
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
