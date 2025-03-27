from dataclasses import dataclass

from sophie_bot.middlewares.connections import ChatConnection


@dataclass
class SophieAIToolContenxt:
    connection: ChatConnection
