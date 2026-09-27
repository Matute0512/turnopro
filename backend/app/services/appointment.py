# app/services/appointment.py
import typing
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.schemas.all_schemas import AppointmentCreate
from app.repositories.appointment import appointment_repo
from app.repositories.customer import customer_repo
from app.repositories.base import BaseRepository
from app.models.all_models import Service

# Instanciamos un repositorio genérico rápido para consultar Servicios
service_repo: BaseRepository[Service] = BaseRepository(Service)


class AppointmentService:
    async def create_appointment(self, db: AsyncSession, data: AppointmentCreate):
        service = await service_repo.get_by_id(db, id=data.service_id)

        # 2. Le aseguramos a Pylance que esto es un bool
        is_active = typing.cast(bool, getattr(service, "is_active", False))

        if not service or not is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El servicio seleccionado no existe o no está activo."
            )

        # 3. Le aseguramos a Pylance que esto es un entero
        duration_minutes = typing.cast(int, service.duration_minutes)
        end_time = data.start_time + timedelta(minutes=duration_minutes)

        # 3. Regla de Negocio: Validar colisión de horarios (Overbooking)
        is_overlap = await appointment_repo.check_overlap(db, data.start_time, end_time)
        if is_overlap:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El horario seleccionado ya no está disponible. Por favor elige otro."
            )

        # 4. Regla de Negocio: Patrón Find-or-Create para el Cliente
        customer = await customer_repo.get_by_phone(db, data.customer_phone)
        if not customer:
            # Si no existe, lo creamos
            customer = await customer_repo.create(db, {
                "full_name": data.customer_full_name,
                "phone": data.customer_phone,
                "email": data.customer_email
            })

        # 5. Guardar la cita inyectando los datos calculados por el servidor (Zero Trust)
        appointment_data = {
            "customer_id": customer.id,
            "service_id": service.id,
            "start_time": data.start_time,
            "end_time": end_time,
            "price_at_booking": service.price,  # Guardamos la foto del precio actual
            "status": "pending"
        }

        return await appointment_repo.create(db, appointment_data)


# Singleton del servicio para inyectarlo en los controladores
appointment_service = AppointmentService()
