# app/api/v1/appointments.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.all_models import Appointment
from app.core.database import get_db
from app.schemas.all_schemas import AppointmentCreate, AppointmentResponse
from app.services.appointment import appointment_service

# Nuevas importaciones para seguridad y lectura de datos
from app.api.deps import get_current_user
from app.models.all_models import User
from app.repositories.appointment import appointment_repo

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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint protegido para el Dashboard.
    Obtiene la lista de todos los turnos programados y carga al cliente asociado.
    """
    stmt = select(Appointment).options(joinedload(Appointment.customer))
    result = await db.execute(stmt)
    return list(result.scalars().all())
