# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.handlers.abstract import MessageHandler


class ErrorTest(MessageHandler):
    @staticmethod
    @router.message(Command("error") & IsSudo)
    async def handle(client: Client, message: Message) -> None:
        msg = "Error Test!"
        raise Exception(msg)
