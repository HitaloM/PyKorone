# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo


@router.message(Command("error", disableable=False) & IsSudo)
async def error_command(client: Client, message: Message) -> None:  # noqa: RUF029
    msg = "Error Test!"
    raise ValueError(msg)
