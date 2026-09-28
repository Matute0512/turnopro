# app/schemas/all_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

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


class ServiceResponse(ServiceBase):
    id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SCHEMAS DE CITAS / TURNOS
# ==========================================
class AppointmentCreate(BaseModel):
    customer_full_name: str = Field(min_length=2, max_length=150)
    customer_phone: str = Field(min_length=8, max_length=20)
    customer_email: Optional[EmailStr] = None

    service_id: UUID
    start_time: datetime


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
