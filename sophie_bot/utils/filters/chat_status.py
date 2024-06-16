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

from aiogram import types
from aiogram.filters import Filter


class OnlyPM(Filter):
    key = 'only_pm'

    def __init__(self, only_pm):
        self.only_pm = only_pm

    async def __call__(self, message: types.Message):
        if message.from_user.id == message.chat.id:
            return True


class OnlyGroups(Filter):
    key = 'only_groups'

    def __init__(self, only_groups):
        self.only_groups = only_groups

    async def __call__(self, message: types.Message):
        if not message.from_user.id == message.chat.id:
            return True
