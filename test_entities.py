from aiogram.types import MessageEntity
from ass_tg.entities import ArgEntities

entities = ArgEntities([MessageEntity(type='bold', offset=0, length=5)])
print(f"ArgEntities methods: {dir(entities)}")
try:
    print(f"entities.index(0): {entities.index(0)}")
except Exception as e:
    print(f"entities.index(0) failed: {e}")
