from typing import Any, Optional

from aiogram.filters import Filter

from sophie_bot.db.models import PrivateNotesModel
from sophie_bot.middlewares.connections import ChatConnection


class PMNotesFilter(Filter):
    async def __call__(self, *args: Any, **kwargs: Any) -> bool:
        connection: Optional[ChatConnection] = kwargs.get("connection")
        if not connection:
            raise ValueError("Missing connection argument in PMNotesFilter.__call__ method")

        if not connection.db_model:
            raise ValueError("Missing db_model in connection")

        private_notes_enabled: bool = await PrivateNotesModel.get_state(connection.db_model.id)

        return private_notes_enabled
