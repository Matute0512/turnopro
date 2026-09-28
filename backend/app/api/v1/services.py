# app/api/v1/services.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.all_schemas import ServiceCreate, ServiceUpdate, ServiceResponse
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
async def get_services(
    skip: int = 0,
    limit: int = 100,
    only_active: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Lista los servicios disponibles (con paginación).

    `only_active=true` es lo que debe consumir el frontend de agendamiento: el
    POST rechaza con 404 los servicios inactivos, así que ofrecerlos en el
    dropdown garantiza un error al confirmar el turno.
    """
    filters = {"is_active": True} if only_active else None
    return await service_repo.get_multi(
        db, skip=skip, limit=limit, order_by=Service.name, filters=filters
    )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    service_in: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza un servicio (Admin)."""
    db_service = await service_repo.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    update_data = service_in.model_dump(exclude_unset=True)
    return await service_repo.update(db, db_obj=db_service, obj_in=update_data)


@router.delete("/{service_id}")
async def delete_service(
    service_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Desactiva un servicio (soft delete).

    NO se borra la fila: `appointments.service_id` la referencia y las citas
    históricas (con su `price_at_booking`) deben seguir siendo auditables. Un
    hard delete sobre un servicio con turnos asociados viola la FK y devuelve
    un 500 sin manejar.
    """
    db_service = await service_repo.get_by_id(db, service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    await service_repo.update(db, db_obj=db_service, obj_in={"is_active": False})
    return {"message": "Servicio desactivado exitosamente"}
