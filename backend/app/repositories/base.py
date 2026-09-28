# app/repositories/base.py
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import Base

# 1. Restauramos el límite. Pylance ahora sabe que ModelType es una tabla SQL
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        # 2. Usamos getattr para extraer el atributo 'id' de forma segura para el linter
        result = await db.execute(select(self.model).filter(getattr(self.model, "id") == id))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        result = await db.execute(select(self.model))
        return list(result.scalars().all())

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        *,
        order_by: Any = None,
        filters: Optional[dict] = None,
    ) -> List[ModelType]:
        """Lista paginada.

        IMPORTANTE: `skip/limit` sin `ORDER BY` NO es una paginación válida.
        Postgres no garantiza el orden de un SELECT sin ORDER BY, por lo que dos
        páginas consecutivas pueden devolver filas repetidas o salteadas. Si no
        se pasa `order_by` explícito, se ordena por PK para que sea determinista.
        """
        stmt = select(self.model)

        for field, value in (filters or {}).items():
            stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.order_by(
            order_by if order_by is not None else getattr(self.model, "id")
        )

        result = await db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, filters: Optional[dict] = None) -> int:
        """Total de filas (para cabeceras de paginación o envelopes {items, total})."""
        stmt = select(func.count()).select_from(self.model)
        for field, value in (filters or {}).items():
            stmt = stmt.where(getattr(self.model, field) == value)
        return (await db.execute(stmt)).scalar_one()

    async def create(self, db: AsyncSession, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        obj = await db.get(self.model, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
