from aiogram.types import Message


async def crash_handler(message: Message):
    await message.reply("Crashing...")

    _ = 1 / 0
