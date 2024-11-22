from unittest.mock import MagicMock

db = MagicMock()
init_db = MagicMock()


def set_db():
    from .db import db, init_db

    global db, init_db
    db = db
    init_db = init_db


__all__ = [
    "db",
]
