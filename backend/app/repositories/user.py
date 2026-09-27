# app/repositories/user.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.all_models import User


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Busca un usuario exactamente por su dirección de email."""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()


user_repo = UserRepository()
