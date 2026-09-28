# app/services/appointment.py
import typing
from datetime import date as date_type
from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.core.timezones import as_utc, business_tz, to_business
from app.models.all_models import Appointment, BusinessSettings, Service
from app.repositories.appointment import appointment_repo
from app.repositories.base import BaseRepository
from app.repositories.customer import customer_repo
from app.schemas.all_schemas import AppointmentCreate

# Instanciamos un repositorio genérico rápido para consultar Servicios
service_repo: BaseRepository[Service] = BaseRepository(Service)
settings_repo: BaseRepository[BusinessSettings] = BaseRepository(BusinessSettings)

# Intervalo de la grilla de turnos (minutos).
SLOT_INTERVAL_MINUTES = 30


class AppointmentService:
    # ------------------------------------------------------------------
    # Configuración comercial
    # ------------------------------------------------------------------
    async def _get_business_config(
        self, db: AsyncSession
    ) -> tuple[list[int], int, int]:
        """Devuelve (work_days, open_hour, close_hour) con defaults seguros."""
        settings_list = await settings_repo.get_multi(db, limit=1)

        work_days = [0, 1, 2, 3, 4, 5]  # Lun-Sab por defecto (Argentina)
        open_h = 9
        close_h = 20

        if settings_list:
            sett = settings_list[0]
            parsed = [
                int(d)
                for d in str(sett.work_days_csv).split(",")
                if d.strip().isdigit()
            ]
            # Un CSV vacío o corrupto NO debe dejar el negocio sin ningún día
            # de atención: eso rechazaría el 100% de las reservas.
            work_days = parsed if parsed else work_days
            open_h = int(sett.open_hour)
            close_h = int(sett.close_hour)

        return work_days, open_h, close_h

    async def _get_active_service(self, db: AsyncSession, service_id) -> Service:
        service = await service_repo.get_by_id(db, id=service_id)
        if not service or not getattr(service, "is_active", False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El servicio seleccionado no existe o no está activo.",
            )
        return service

    # ------------------------------------------------------------------
    # POST /appointments/
    # ------------------------------------------------------------------
    async def create_appointment(self, db: AsyncSession, data: AppointmentCreate):
        service = await self._get_active_service(db, data.service_id)

        # Le aseguramos a Pylance que esto es un entero
        duration_minutes = typing.cast(int, service.duration_minutes)

        # 1. Normalizamos el instante recibido y lo expresamos en hora del local.
        #    Antes se comparaba el valor crudo (UTC) contra open_hour/close_hour,
        #    lo que corría el horario comercial 3 horas en Argentina.
        start_local = to_business(data.start_time)
        start_utc = start_local.astimezone(timezone.utc)

        # 2. Regla de Negocio: Validar fechas en el pasado.
        if start_utc < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pueden agendar turnos en el pasado.",
            )

        # 3. Regla de Negocio: Horario Comercial Dinámico, SIEMPRE en hora local.
        work_days, open_h, close_h = await self._get_business_config(db)

        # weekday(): 0 es Lunes, 6 es Domingo. Se evalúa sobre el día LOCAL:
        # un sábado 21:00 ART es domingo 00:00 UTC, y mirar el UTC rechazaba
        # reservas válidas de fin de día.
        if start_local.weekday() not in work_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El local no atiende en este día de la semana.",
            )

        # Comparamos en minutos desde medianoche: sin floats y sin ambigüedad.
        start_minutes = start_local.hour * 60 + start_local.minute
        end_minutes = start_minutes + duration_minutes
        open_minutes = open_h * 60
        close_minutes = close_h * 60

        if start_minutes < open_minutes or end_minutes > close_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El horario de atención es de {open_h:02d}:00 "
                    f"a {close_h:02d}:00."
                ),
            )

        end_local = start_local + timedelta(minutes=duration_minutes)
        if end_local.date() != start_local.date():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El turno no puede extenderse más allá de la medianoche.",
            )

        end_utc = end_local.astimezone(timezone.utc)

        # 4. Regla de Negocio: Validar colisión de horarios (Overbooking).
        #    Se compara en UTC contra lo persistido: mismo marco en ambos lados.
        if await appointment_repo.check_overlap(db, start_utc, end_utc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El horario seleccionado ya no está disponible. Por favor elige otro.",
            )

        # 5. Regla de Negocio: Patrón Find-or-Create para el Cliente.
        customer = await customer_repo.get_by_phone(db, data.customer_phone)
        if not customer:
            customer = await customer_repo.create(db, {
                "full_name": data.customer_full_name,
                "phone": data.customer_phone,
                "email": data.customer_email,
            })

        # 6. Persistimos en UTC (nunca la hora local del local).
        new_appointment = await appointment_repo.create(db, {
            "customer_id": customer.id,
            "service_id": service.id,
            "start_time": start_utc,
            "end_time": end_utc,
            "price_at_booking": service.price,  # Foto del precio actual
            "status": "pending",
        })

        # 7. Eager Loading: serializar `customer_full_name` accede a la relación.
        #    En Async un lazy-load implícito genera MissingGreenlet.
        stmt = (
            select(Appointment)
            .options(
                joinedload(Appointment.customer),
                joinedload(Appointment.service),
            )
            .where(Appointment.id == new_appointment.id)
        )
        return (await db.execute(stmt)).scalar_one()

    # ------------------------------------------------------------------
    # GET /appointments/available-slots
    # ------------------------------------------------------------------
    async def get_available_slots(
        self, db: AsyncSession, target_date: date_type, service_id
    ) -> list[str]:
        """Calcula los horarios libres de un día como ISO-8601 CON offset.

        Devolver el instante completo (ej. "2026-10-01T09:00:00-03:00") en vez
        de un "HH:MM" pelado es lo que elimina la ambigüedad de raíz: el cliente
        no tiene que adivinar en qué zona horaria está ese "09:00", solo
        devolver el mismo string en el POST.
        """
        # 1. Validar el servicio para conocer su duración.
        service = await self._get_active_service(db, service_id)
        duration_minutes = typing.cast(int, service.duration_minutes)

        # 2. Obtener la configuración del negocio.
        work_days, open_h, close_h = await self._get_business_config(db)

        # Si el local está cerrado ese día, no hay nada que ofrecer.
        if target_date.weekday() not in work_days:
            return []

        tz = business_tz()

        # 3. Ventana del día COMERCIAL (local) expresada en UTC, para consultar.
        #    Antes se usaba el día UTC, lo que corría la ventana de búsqueda de
        #    turnos existentes y hacía que la grilla detectara solapamientos en
        #    el horario equivocado.
        day_start_utc = datetime.combine(
            target_date, time.min, tzinfo=tz
        ).astimezone(timezone.utc)
        day_end_utc = datetime.combine(
            target_date + timedelta(days=1), time.min, tzinfo=tz
        ).astimezone(timezone.utc)

        stmt_apts = select(Appointment).where(
            Appointment.start_time >= day_start_utc,
            Appointment.start_time < day_end_utc,
            Appointment.status != "cancelled",
        )
        existing_apts = (await db.execute(stmt_apts)).scalars().all()

        # Normalizamos a UTC: en SQLite los valores vuelven naive.
        busy_ranges = [
            (
                as_utc(apt.start_time),
                as_utc(apt.end_time),
            )
            for apt in existing_apts
        ]

        now_utc = datetime.now(timezone.utc)
        open_minutes = open_h * 60
        close_minutes = close_h * 60

        slots: list[str] = []
        current_minutes = open_minutes

        while current_minutes + duration_minutes <= close_minutes:
            # El slot se construye en hora LOCAL y se compara en UTC.
            slot_start_utc = (
                datetime.combine(target_date, time.min, tzinfo=tz)
                + timedelta(minutes=current_minutes)
            ).astimezone(timezone.utc)
            slot_end_utc = slot_start_utc + timedelta(minutes=duration_minutes)
            current_minutes += SLOT_INTERVAL_MINUTES

            # Si el turno propuesto ya pasó, lo saltamos.
            if slot_start_utc < now_utc:
                continue

            # Colisión: max(start1, start2) < min(end1, end2). Mismo marco (UTC).
            if any(
                max(slot_start_utc, busy_start) < min(slot_end_utc, busy_end)
                for busy_start, busy_end in busy_ranges
            ):
                continue

            slots.append(slot_start_utc.astimezone(tz).isoformat())

        return slots


# Singleton del servicio para inyectarlo en los controladores
appointment_service = AppointmentService()
