# app/repositories/customer.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.all_models import Customer


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self):
        super().__init__(Customer)

    async def get_by_phone(self, db: AsyncSession, phone: str) -> Optional[Customer]:
        """Busca un cliente exacto por su número de teléfono."""
        result = await db.execute(select(Customer).filter(Customer.phone == phone))
        return result.scalar_one_or_none()


customer_repo = CustomerRepository()
