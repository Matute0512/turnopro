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

        # 3. Regla de Negocio: Validar fechas en el pasado
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if data.start_time < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden agendar turnos en el pasado."
            )

        # 4. Regla de Negocio: Validar Horario Comercial Dinámico (Settings)
        from app.models.all_models import BusinessSettings
        from sqlalchemy.future import select

        stmt = select(BusinessSettings)
        result = await db.execute(stmt)
        settings_list = result.scalars().all()

        # Valores por defecto en caso de que aún no existan en DB
        work_days = [0, 1, 2, 3, 4, 5]  # Lun-Sab por defecto (Argentina)
        open_h = 9
        close_h = 20

        if settings_list:
            sett = settings_list[0]
            work_days = [int(d) for d in str(sett.work_days_csv).split(
                ",") if d.strip().isdigit()]
            open_h = int(sett.open_hour)
            close_h = int(sett.close_hour)

        # weekday(): 0 es Lunes, 6 es Domingo
        if data.start_time.weekday() not in work_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El local no atiende en este día de la semana."
            )

        # 5. Le aseguramos a Pylance que esto es un entero
        duration_minutes = typing.cast(int, service.duration_minutes)
        end_time = data.start_time + timedelta(minutes=duration_minutes)

        start_hour = data.start_time.hour + (data.start_time.minute / 60.0)
        end_hour = end_time.hour + (end_time.minute / 60.0)

        if start_hour < open_h or end_hour > close_h:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El horario de atención es de {open_h}:00 a {close_h}:00."
            )

        # 6. Regla de Negocio: Validar colisión de horarios (Overbooking)
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

        new_appointment = await appointment_repo.create(db, appointment_data)

        # 6. Eager Loading: FastAPI intentará acceder a properties como customer_full_name
        # Como estamos en Async, acceder a lazy-loads genera MissingGreenlet.
        # Forzamos la carga de la relación cliente y servicio.
        from sqlalchemy.future import select
        from sqlalchemy.orm import joinedload
        from app.models.all_models import Appointment

        stmt = select(Appointment).options(
            joinedload(Appointment.customer),
            joinedload(Appointment.service)
        ).where(Appointment.id == new_appointment.id)

        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_available_slots(self, db: AsyncSession, target_date: str, service_id: str) -> list[str]:
        """Calcula y devuelve los horarios (HH:MM) disponibles para un día específico."""
        from datetime import datetime, timezone, time

        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD.")

        # 1. Validar si el servicio existe para calcular intervalos (duration_minutes)
        service = await service_repo.get_by_id(db, id=service_id)
        if not service or not getattr(service, "is_active", False):
            raise HTTPException(status_code=404, detail="Servicio inválido.")
        duration_minutes = typing.cast(int, service.duration_minutes)

        # 2. Obtener la configuración del negocio
        from app.models.all_models import BusinessSettings
        from sqlalchemy.future import select
        stmt = select(BusinessSettings)
        result = await db.execute(stmt)
        settings_list = result.scalars().all()

        work_days = [0, 1, 2, 3, 4, 5]
        open_h = 9
        close_h = 20
        if settings_list:
            sett = settings_list[0]
            work_days = [int(d) for d in str(
                sett.work_days_csv).split(",") if d.strip().isdigit()]
            open_h = int(sett.open_hour)
            close_h = int(sett.close_hour)

        # Si el local está cerrado ese día, retornar vacío
        if date_obj.weekday() not in work_days:
            return []

        # 3. Obtener turnos existentes en ese día
        # Asumiendo UTC por defecto (para MVP simplificado)
        start_of_day = datetime.combine(
            date_obj, time.min).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(
            date_obj, time.max).replace(tzinfo=timezone.utc)

        from app.models.all_models import Appointment
        # Consultar todos los turnos confirmados/pendientes del día
        stmt_apts = select(Appointment).where(
            Appointment.start_time >= start_of_day,
            Appointment.start_time <= end_of_day,
            Appointment.status != 'cancelled'
        )
        existing_apts = (await db.execute(stmt_apts)).scalars().all()

        # 4. Generar slots (intervalos de 30 mins, o la duración del servicio)
        # Para peluquerías lo normal es intervalos cada 30 min y ver si entra la duración total
        interval_minutes = 30
        slots_available = []

        current_time = datetime.combine(date_obj, time(
            hour=open_h)).replace(tzinfo=timezone.utc)
        close_time = datetime.combine(date_obj, time(
            hour=close_h)).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        while current_time + timedelta(minutes=duration_minutes) <= close_time:
            # Si el turno propuesto es en el pasado, lo saltamos
            if current_time < now:
                current_time += timedelta(minutes=interval_minutes)
                continue

            slot_end = current_time + timedelta(minutes=duration_minutes)
            overlap = False

            for apt in existing_apts:
                # Condición de colisión (Overlap)
                # Max(start1, start2) < Min(end1, end2)
                if max(current_time, apt.start_time) < min(slot_end, apt.end_time):
                    overlap = True
                    break

            if not overlap:
                slots_available.append(current_time.strftime("%H:%M"))

            current_time += timedelta(minutes=interval_minutes)

        return slots_available


# Singleton del servicio para inyectarlo en los controladores
appointment_service = AppointmentService()
