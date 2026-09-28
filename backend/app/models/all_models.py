# app/models/all_models.py
import uuid
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # Usamos UUID por seguridad contra ataques IDOR
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación: Un admin tiene muchos registros de auditoria
    audit_logs = relationship("AuditLog", back_populates="user")


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)

    appointments = relationship("Appointment", back_populates="service")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)

    appointments = relationship("Appointment", back_populates="customer")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey(
        "customers.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey(
        "services.id"), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Inmutabilidad financiera
    price_at_booking = Column(Numeric(10, 2), nullable=False)
    # pending, confirmed, cancelled
    status = Column(String(20), nullable=False, default="pending")

    customer = relationship("Customer", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

    @property
    def customer_full_name(self) -> str:
        return self.customer.full_name if self.customer else ""

    @property
    def customer_phone(self) -> str:
        return self.customer.phone if self.customer else ""


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=False)  # Soporta IPv6
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")

class BusinessSettings(Base):
    __tablename__ = "business_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_days_csv = Column(String(50), nullable=False, default="0,1,2,3,4,5")
    open_hour = Column(Integer, nullable=False, default=9)
    close_hour = Column(Integer, nullable=False, default=18)
