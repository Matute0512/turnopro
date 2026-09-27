# app/api/v1/appointments.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.all_schemas import AppointmentCreate, AppointmentResponse
from app.services.appointment import appointment_service

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
