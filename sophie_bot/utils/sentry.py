# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
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

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.pymongo import PyMongoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from sophie_bot import SOPHIE_VERSION
from sophie_bot.config import CONFIG
from sophie_bot.utils.logger import log


def init_sentry():
    log.info("Starting sentry.io integraion...")

    sentry_sdk.init(
        str(CONFIG.sentry_url),
        integrations=[RedisIntegration(), AioHttpIntegration(), PyMongoIntegration()],
        environment=CONFIG.environment,
        release=SOPHIE_VERSION,
    )
