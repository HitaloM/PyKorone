from datetime import timedelta

from sophie_bot.modules.legacy_modules.utils.message import convert_time
from sophie_bot.modules.legacy_modules.utils.restrictions import restrict_user


async def on_welcomemute(group_id: int, user_id: int, on_time: str | timedelta):
    await restrict_user(
        group_id,
        user_id,
        until_date=convert_time(on_time),
    )
