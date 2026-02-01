from korone.db.base import get_one
from korone.db.models.disabling import DisablingModel
from korone.db.session import session_scope


async def get_disabled(chat_id: int) -> list[str]:
    async with session_scope() as session:
        model = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)
    return list(model.cmds) if model and model.cmds else []


async def disable(chat_id: int, cmd: str) -> DisablingModel:
    async with session_scope() as session:
        if model := await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id):
            if cmd not in (model.cmds or []):
                model.cmds = [*model.cmds, cmd]
            return model

        model = DisablingModel(chat_id=chat_id, cmds=[cmd])
        session.add(model)
        await session.flush()
        return model


async def enable(chat_id: int, cmd: str) -> DisablingModel:
    async with session_scope() as session:
        model = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)
        if not model or cmd not in (model.cmds or []):
            msg = "Disabled command not found"
            raise LookupError(msg)

        model.cmds = [c for c in model.cmds if c != cmd]
        return model


async def enable_all(chat_id: int) -> DisablingModel | None:
    async with session_scope() as session:
        if model := await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id):
            await session.delete(model)
            return model
    return None


async def set_disabled(chat_id: int, cmds: list[str]) -> DisablingModel:
    async with session_scope() as session:
        if model := await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id):
            model.cmds = cmds
            return model

        model = DisablingModel(chat_id=chat_id, cmds=cmds)
        session.add(model)
        await session.flush()
        return model
