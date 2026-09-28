from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.all_schemas import CustomerResponse
from app.repositories.base import BaseRepository
from app.models.all_models import Customer, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/customers", tags=["Customers"])
customer_repo = BaseRepository(Customer)


@router.get("/", response_model=list[CustomerResponse])
async def get_customers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la lista de todos los clientes registrados (con paginación)."""
    return await customer_repo.get_multi(db, skip=skip, limit=limit)
