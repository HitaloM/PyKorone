# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import logging
from datetime import datetime, timezone

import sentry_sdk
from pyrogram import Client, __version__
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import BadRequest
from pyrogram.helpers import ikb
from pyrogram.raw.all import layer
from pyrogram.types import Message, User

import korone
from korone.config import API_HASH, API_ID, LOGS_CHANNEL, SENTRY_KEY, SUDOERS, TOKEN
from korone.utils import shell_exec

log = logging.getLogger(__name__)


class Korone(Client):
    def __init__(self):
        name = self.__class__.__name__.lower()

        super().__init__(
            name=name,
            app_version=f"PyKorone v{korone.__version__}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=TOKEN,
            parse_mode=ParseMode.HTML,
            workers=24,
            workdir="korone",
            plugins=dict(root="korone.handlers"),
            sleep_threshold=180,
        )

        self.sudos = SUDOERS

        # Save start time (useful for uptime info)
        self.start_time = datetime.now().replace(tzinfo=timezone.utc)

    async def start(self):
        await super().start()

        # Save version info
        self.version_code = int((await shell_exec("git rev-list --count HEAD"))[0])
        self.version = str((await shell_exec("git rev-parse --short HEAD"))[0])

        # Some useful vars
        self.me = await self.get_me()
        self.ikb = ikb

        if not SENTRY_KEY or SENTRY_KEY == "":
            log.warning("No sentry.io key found! Service not initialized.")
        else:
            log.info("Starting sentry.io service.")
            sentry_sdk.init(SENTRY_KEY, traces_sample_rate=1.0)

        log.info(
            "PyKorone for Pyrogram v%s (Layer %s) started on @%s. Hi.",
            __version__,
            layer,
            self.me.username,
        )

        # Startup message
        try:
            for sudo in self.sudos:
                await self.send_message(
                    chat_id=sudo,
                    text=(
                        f"<b>PyKorone</b> <a href='https://github.com/AmanoTeam/PyKorone/commit/{self.version}'>{self.version}</a> (<code>{self.version_code}</code>) started!"
                        f"\n<b>Pyrogram</b> <code>v{__version__}</code> (Layer {layer})"
                    ),
                    disable_web_page_preview=True,
                )
        except BadRequest:
            log.error("Error while sending the startup message.", exc_info=True)

    async def restart(self, *args):
        log.info("PyKorone client is restarting...")
        await super().restart(*args)

    async def stop(self, *args):
        await super().stop(*args)
        log.info("PyKorone stopped... Bye.")

    async def int_reply(self, m: Message, text: str, *args, **kwargs):
        if m.chat.type == ChatType.PRIVATE:
            await m.reply_text(text, *args, **kwargs)
        elif m.reply_to_message and (
            m.reply_to_message.from_user is not None
            and m.reply_to_message.from_user.id == self.me.id
        ):
            await m.reply_text(text, *args, **kwargs)
        return

    async def send_log(self, text: str, *args, **kwargs):
        await self.send_message(
            chat_id=LOGS_CHANNEL,
            text=text,
            *args,
            **kwargs,
        )
        return

    def is_sudoer(self, user: User) -> bool:
        return user.id in self.sudos
