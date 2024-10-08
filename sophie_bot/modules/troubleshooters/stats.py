from stfu_tg import KeyValue, Section
from stfu_tg.doc import Element

from sophie_bot.db.models import BetaModeModel, GlobalSettings


async def beta_stats() -> Element:
    percentage_db = await GlobalSettings.get_by_key("beta_percentage")
    percentage = percentage_db.value if percentage_db else 0

    beta_chats = await BetaModeModel.beta_mode_chats_count()
    total_chats = await BetaModeModel.count()
    calculated_percentage = int((beta_chats / total_chats) * 100)

    return Section(
        KeyValue("New chats Beta percentage", f"{percentage}%"),
        KeyValue("Total beta chats", f"{beta_chats}"),
        KeyValue("Calculated beta percentage", f"{calculated_percentage}%"),
        title="Beta",
    )
