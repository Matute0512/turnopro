# app/api/v1/services.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.all_schemas import ServiceCreate, ServiceResponse
from app.repositories.base import BaseRepository
from app.models.all_models import Service, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])

# Instanciamos el repositorio genérico para la entidad Service
service_repo = BaseRepository(Service)


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuevo servicio en el catálogo."""
    # Convertimos el modelo Pydantic a diccionario con model_dump()
    return await service_repo.create(db, obj_in=service_in.model_dump())


@router.get("/", response_model=list[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    """Lista todos los servicios disponibles."""
    return await service_repo.get_all(db)
