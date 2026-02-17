from sqlalchemy import delete, func, select, update

from korone.db.base import get_one
from korone.db.models.sticker_pack import StickerPackModel
from korone.db.session import session_scope


class StickerPackRepository:
    @staticmethod
    async def total_count() -> int:
        async with session_scope() as session:
            result = await session.execute(select(func.count()).select_from(StickerPackModel))
            return int(result.scalar_one() or 0)

    @staticmethod
    async def unique_owner_count() -> int:
        async with session_scope() as session:
            result = await session.execute(select(func.count(func.distinct(StickerPackModel.owner_id))))
            return int(result.scalar_one() or 0)

    @staticmethod
    async def list_user_packs(owner_id: int) -> list[StickerPackModel]:
        async with session_scope() as session:
            result = await session.execute(
                select(StickerPackModel)
                .where(StickerPackModel.owner_id == owner_id)
                .order_by(
                    StickerPackModel.is_default.desc(), StickerPackModel.created_at.asc(), StickerPackModel.id.asc()
                )
            )
            return list(result.scalars().all())

    @staticmethod
    async def get_by_pack_id(pack_id: str) -> StickerPackModel | None:
        async with session_scope() as session:
            return await get_one(session, StickerPackModel, StickerPackModel.pack_id == pack_id)

    @staticmethod
    async def get_default_pack(owner_id: int) -> StickerPackModel | None:
        async with session_scope() as session:
            return await get_one(
                session, StickerPackModel, StickerPackModel.owner_id == owner_id, StickerPackModel.is_default.is_(True)
            )

    @staticmethod
    async def get_by_title(owner_id: int, title: str) -> StickerPackModel | None:
        normalized_title = title.strip().lower()
        async with session_scope() as session:
            stmt = select(StickerPackModel).where(
                StickerPackModel.owner_id == owner_id, func.lower(StickerPackModel.title) == normalized_title
            )
            result = await session.execute(stmt.limit(1))
            return result.scalars().first()

    @staticmethod
    async def upsert_pack(
        pack_id: str, owner_id: int, title: str, *, set_default: bool | None = None
    ) -> StickerPackModel:
        normalized_title = title.strip()[:64]
        async with session_scope() as session:
            item = await get_one(session, StickerPackModel, StickerPackModel.pack_id == pack_id)

            if item:
                item.owner_id = owner_id
                item.title = normalized_title
            else:
                item = StickerPackModel(pack_id=pack_id, owner_id=owner_id, title=normalized_title)
                session.add(item)
                await session.flush()

            if set_default is True:
                await session.execute(
                    update(StickerPackModel).where(StickerPackModel.owner_id == owner_id).values(is_default=False)
                )
                item.is_default = True
                return item

            if set_default is False:
                return item

            default_pack = await get_one(
                session, StickerPackModel, StickerPackModel.owner_id == owner_id, StickerPackModel.is_default.is_(True)
            )
            if default_pack is None:
                item.is_default = True

            return item

    @staticmethod
    async def set_default_by_pack_id(owner_id: int, pack_id: str) -> StickerPackModel | None:
        async with session_scope() as session:
            item = await get_one(
                session, StickerPackModel, StickerPackModel.owner_id == owner_id, StickerPackModel.pack_id == pack_id
            )
            if not item:
                return None

            await session.execute(
                update(StickerPackModel).where(StickerPackModel.owner_id == owner_id).values(is_default=False)
            )
            item.is_default = True
            return item

    @staticmethod
    async def set_default_by_title(owner_id: int, title: str) -> StickerPackModel | None:
        normalized_title = title.strip().lower()
        async with session_scope() as session:
            stmt = select(StickerPackModel).where(
                StickerPackModel.owner_id == owner_id, func.lower(StickerPackModel.title) == normalized_title
            )
            result = await session.execute(stmt.limit(1))
            item = result.scalars().first()

            if not item:
                return None

            await session.execute(
                update(StickerPackModel).where(StickerPackModel.owner_id == owner_id).values(is_default=False)
            )
            item.is_default = True
            return item

    @staticmethod
    async def delete_pack(pack_id: str) -> int:
        async with session_scope() as session:
            result = await session.execute(
                delete(StickerPackModel).where(StickerPackModel.pack_id == pack_id).returning(StickerPackModel.id)
            )
            return len(result.scalars().all())

    @staticmethod
    async def delete_packs(pack_ids: list[str]) -> int:
        if not pack_ids:
            return 0

        async with session_scope() as session:
            result = await session.execute(
                delete(StickerPackModel).where(StickerPackModel.pack_id.in_(pack_ids)).returning(StickerPackModel.id)
            )
            return len(result.scalars().all())
