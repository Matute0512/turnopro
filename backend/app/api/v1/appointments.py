# app/api/v1/appointments.py
from datetime import date as date_type
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.all_models import Appointment, User
from app.core.database import get_db
from app.schemas.all_schemas import AppointmentCreate, AppointmentResponse
from app.services.appointment import appointment_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint público para agendar un turno.
    Delega toda la validación y persistencia a la Capa de Servicios.
    """
    return await appointment_service.create_appointment(db=db, data=appointment_in)


@router.get("/", response_model=list[AppointmentResponse])
async def get_appointments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint protegido para el Dashboard.
    Obtiene la lista de los turnos programados y carga al cliente asociado.
    """
    stmt = (
        select(Appointment)
        .options(joinedload(Appointment.customer))
        # ORDER BY es OBLIGATORIO cuando se usa skip/limit: sin él Postgres no
        # garantiza el orden de las filas, así que dos páginas consecutivas
        # pueden repetir o saltear turnos.
        .order_by(Appointment.start_time)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/available-slots", response_model=list[str])
async def get_available_slots(
    # Tipos nativos en vez de `str`: FastAPI valida el formato en el borde y
    # devuelve 422, en lugar de mandar un string crudo a la DB (que reventaba
    # con StatementError -> 500 en vez de un error de validación).
    date: date_type,
    service_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Devuelve los horarios libres (ISO-8601 con offset) de un día y servicio."""
    return await appointment_service.get_available_slots(
        db=db, target_date=date, service_id=service_id
    )
