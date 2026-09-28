# app/core/timezones.py
"""Utilidades de zona horaria para TurnoPro.

Regla de arquitectura (Zero Trust temporal):
  - En la base de datos TODO se persiste en UTC (`DateTime(timezone=True)`).
  - Las reglas de NEGOCIO (día de atención, apertura/cierre, grilla de slots)
    se evalúan SIEMPRE en la zona horaria del local, nunca en UTC ni en la
    zona del dispositivo del cliente.

Hay TRES funciones y no una porque un datetime naive es ambiguo y el
significado depende de su origen:
  - `to_business()`  -> viene de un cliente HTTP: naive significa hora del local
                        (es la hora que el usuario vio en pantalla).
  - `as_utc()`       -> viene de la DB: naive significa UTC (SQLite no guarda
                        el offset; Postgres sí, y devuelve aware).
  - `to_utc()`       -> azúcar para normalizar una entrada de cliente a UTC.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

_BUSINESS_TZ: "ZoneInfo | None" = None


def business_tz() -> ZoneInfo:
    """Zona horaria del local (cacheada).

    Requiere el paquete `tzdata` en Windows: la base de datos IANA no viene
    incluida con el sistema operativo y `ZoneInfo` falla con
    `ZoneInfoNotFoundError` si no está instalado.
    """
    global _BUSINESS_TZ
    if _BUSINESS_TZ is None:
        _BUSINESS_TZ = ZoneInfo(settings.BUSINESS_TIMEZONE)
    return _BUSINESS_TZ


def to_business(dt: datetime) -> datetime:
    """Normaliza un datetime recibido de un cliente a la zona horaria del local.

    Un datetime SIN offset es ambiguo. Acá lo interpretamos como hora del local
    (es lo que el usuario vio en pantalla) en vez de asumir UTC a ciegas: eso
    evita tanto el TypeError de comparar naive contra aware como el
    desplazamiento silencioso del turno varias horas.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=business_tz())
    return dt.astimezone(business_tz())


def as_utc(dt: datetime) -> datetime:
    """Interpreta un valor leído de la BASE DE DATOS como UTC.

    Es deliberadamente distinto de `to_business()`: acá un naive significa UTC,
    porque el contrato de almacenamiento es "siempre UTC". En Postgres los
    valores vuelven aware; en SQLite (el motor de la suite de tests) vuelven
    naive, y asumir hora local desplazaría los turnos 3 horas y rompería la
    detección de solapamientos con un TypeError.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convierte una entrada de cliente a UTC-aware (formato de persistencia)."""
    return to_business(dt).astimezone(timezone.utc)
