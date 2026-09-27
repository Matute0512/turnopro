# app/repositories/appointment.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.all_models import Appointment


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        # Inicializamos la clase padre pasándole el modelo Appointment
        super().__init__(Appointment)

    async def check_overlap(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> bool:
        """
        Verifica si existe alguna cita confirmada o pendiente que se superponga
        con el rango de tiempo solicitado. Devuelve True si hay superposición (conflicto).
        """
        # La fórmula matemática para detectar colisión de dos rangos de tiempo (A y B) es:
        # (StartA < EndB) AND (EndA > StartB)
        stmt = select(Appointment).filter(
            Appointment.status.in_(["pending", "confirmed"]),
            and_(
                Appointment.start_time < end_time,
                Appointment.end_time > start_time
            )
        )

        result = await db.execute(stmt)
        overlapping_appointment = result.scalars().first()

        # Si encuentra una cita, significa que el horario está ocupado (True)
        return overlapping_appointment is not None


# Instanciamos el repositorio para usarlo en nuestra capa de servicios (Singleton pattern simple)
appointment_repo = AppointmentRepository()
