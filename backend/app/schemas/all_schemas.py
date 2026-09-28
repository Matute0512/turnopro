# app/schemas/all_schemas.py
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_serializer,
    model_validator,
)
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.core.timezones import as_utc

# ==========================================
# SCHEMAS DE USUARIO (DUEÑO/ADMIN)
# ==========================================


class UserBase(BaseModel):
    email: EmailStr  # Pydantic valida que sea un email real


class UserCreate(UserBase):
    # Validamos que la contraseña tenga al menos 8 caracteres
    password: str = Field(
        min_length=8, description="Contraseña en texto plano")


class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    # Esto le dice a Pydantic que este esquema puede leer datos
    # de un objeto de SQLAlchemy (ORM), no solo de un diccionario.
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SCHEMAS DE SERVICIOS
# ==========================================
class ServiceBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    duration_minutes: int = Field(
        gt=0, description="Duración en minutos (debe ser mayor a 0)")
    price: Decimal = Field(
        ge=0, description="Precio del servicio (no puede ser negativo)")


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE CONFIGURACIÓN
# ==========================================


class BusinessSettingsUpdate(BaseModel):
    # 0=Lunes ... 6=Domingo. Se valida el formato para que un CSV corrupto no
    # deje el negocio sin ningún día de atención (eso vaciaría la grilla de
    # turnos en silencio, sin ningún error visible).
    work_days_csv: Optional[str] = Field(
        None,
        pattern=r"^\s*[0-6]\s*(,\s*[0-6]\s*)*$",
        description="Días de atención: 0=Lunes ... 6=Domingo. Ej: '0,1,2,3,4,5'",
    )
    open_hour: Optional[int] = Field(None, ge=0, le=23)
    close_hour: Optional[int] = Field(None, ge=0, le=23)

    @model_validator(mode="after")
    def _rango_coherente(self):
        if (
            self.open_hour is not None
            and self.close_hour is not None
            and self.open_hour >= self.close_hour
        ):
            raise ValueError("open_hour debe ser menor que close_hour")
        return self


class BusinessSettingsResponse(BaseModel):
    id: UUID
    work_days_csv: str
    open_hour: int
    close_hour: int
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SCHEMAS DE CITAS / TURNOS
# ==========================================
class CustomerResponse(BaseModel):
    id: UUID
    full_name: str
    phone: str
    email: Optional[EmailStr] = None
    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    customer_full_name: str = Field(min_length=2, max_length=150)
    customer_phone: str = Field(min_length=8, max_length=20)
    customer_email: Optional[EmailStr] = None

    service_id: UUID
    # `AwareDatetime` exige que el cliente mande el offset explícito. Un naive
    # es ambiguo (¿hora del local? ¿UTC?) y antes rompía con TypeError al
    # compararse contra `datetime.now(timezone.utc)`. Sin offset -> 422.
    start_time: AwareDatetime


class AppointmentResponse(BaseModel):
    id: UUID
    customer_id: UUID
    service_id: UUID
    start_time: datetime
    end_time: datetime
    price_at_booking: Decimal
    status: str

    customer_full_name: Optional[str] = None
    customer_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("start_time", "end_time")
    def _serialize_utc(self, value: datetime):
        """Fuerza el offset en la respuesta.

        El frontend hace `DateTime.parse(...).toLocal()`: si el string viniera
        sin offset (lo que ocurre cuando el driver devuelve un datetime naive),
        Dart lo interpretaría como hora local del dispositivo y el turno
        aparecería corrido varias horas en el calendario.
        """
        return as_utc(value).isoformat()
