# backend/tests/test_appointments.py
from datetime import date, datetime, timedelta

import pytest

from app.api.v1.settings import DEFAULT_OPEN_HOUR
from app.core.timezones import business_tz

# Le decimos a pytest que estas pruebas usan asyncio
pytestmark = pytest.mark.asyncio

SERVICE_PAYLOAD = {
    "name": "Corte Test",
    "duration_minutes": 30,
    "price": 1000,
}


def at(day: date, hour: int, minute: int = 0) -> str:
    """ISO-8601 con offset de una hora LOCAL del negocio.

    Los tests anteriores mandaban "10:00:00Z" y asumían que UTC era la hora del
    local: eso codificaba el mismo bug que se está corrigiendo (con el negocio
    en UTC-3, las 10:00Z son las 07:00 locales, fuera del horario de atención).
    """
    return datetime(
        day.year, day.month, day.day, hour, minute, tzinfo=business_tz()
    ).isoformat()


def next_open_day(days_ahead: int = 7) -> date:
    """Primer día de atención a partir de hoy + days_ahead (defaults: Lun-Sab)."""
    day = date.today() + timedelta(days=days_ahead)
    while day.weekday() > 5:  # 6 = Domingo
        day += timedelta(days=1)
    return day


async def create_service(client) -> str:
    response = await client.post("/api/v1/services/", json=SERVICE_PAYLOAD)
    assert response.status_code == 201
    return response.json()["id"]


async def get_slots(client, day: date, service_id: str) -> list[str]:
    response = await client.get(
        "/api/v1/appointments/available-slots",
        params={"date": day.isoformat(), "service_id": service_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def book(client, day: date, hour: int, minute: int, service_id: str, phone: str):
    return await client.post("/api/v1/appointments/", json={
        "customer_full_name": "Cliente Test",
        "customer_phone": phone,
        "service_id": service_id,
        "start_time": at(day, hour, minute),
    })


# ----------------------------------------------------------------------
# Prevención de overbooking
# ----------------------------------------------------------------------
async def test_appointment_overlap_prevention(client):
    """
    Prueba End-to-End simulada:
    1. Crea un servicio de 30 min.
    2. Agenda un turno a las 10:00 (Exitoso).
    3. Intenta agendar a las 10:15 (Debe fallar - Conflicto 409).
    4. Intenta agendar a las 10:30 (Exitoso - Empieza al terminar el anterior).
    """
    day = next_open_day()
    service_id = await create_service(client)

    # PASO 2: Agendar el primer turno (10:00 AM hora del local)
    res_1 = await book(client, day, 10, 0, service_id, "11111111")
    assert res_1.status_code == 201, res_1.text

    # PASO 3: Intentar pisar el turno (10:15 AM) - DEBE FALLAR
    res_2 = await book(client, day, 10, 15, service_id, "22222222")
    assert res_2.status_code == 409  # HTTP 409: Conflict

    # PASO 4: Agendar justo al terminar el primero (10:30 AM) - DEBE PASAR
    res_3 = await book(client, day, 10, 30, service_id, "33333333")
    assert res_3.status_code == 201, res_3.text


# ----------------------------------------------------------------------
# REGRESION: consistencia entre available-slots y POST /appointments/
# ----------------------------------------------------------------------
async def test_all_offered_slots_are_bookable(client):
    """Todo horario OFRECIDO por /available-slots debe poder reservarse.

    Es el invariante que estaba roto: la grilla se generaba en UTC pero el POST
    validaba el horario comercial contra la hora local del payload, así que los
    últimos 6 chips del día (17:00 a 19:30) se ofrecían y después se rechazaban
    con 400 "El horario de atención es de 09:00 a 20:00".
    """
    day = next_open_day()
    service_id = await create_service(client)
    slots = await get_slots(client, day, service_id)

    assert slots, "La grilla de un día hábil no debería estar vacía"

    for index, slot in enumerate(slots):
        response = await client.post("/api/v1/appointments/", json={
            "customer_full_name": "Cliente Test",
            "customer_phone": f"4000{index:04d}",
            "service_id": service_id,
            "start_time": slot,
        })
        assert response.status_code == 201, (
            f"El slot {slot} fue ofrecido por /available-slots pero el POST "
            f"devolvió {response.status_code}: {response.text}"
        )


async def test_reserved_slot_disappears_and_no_other_slot_changes(client):
    """Reservar un turno quita ESE chip de la grilla y ningún otro.

    Detecta el bug de la grilla rotada: /available-slots comparaba los slots en
    marco UTC-etiqueta contra citas persistidas en UTC real, así que reservar
    las 10:00 ocultaba las 13:00 y dejaba las 10:00 visibles como libres (el
    usuario las volvía a elegir y recibía un 409).
    """
    day = next_open_day()
    service_id = await create_service(client)

    slots_before = await get_slots(client, day, service_id)
    assert len(slots_before) >= 3, "Se necesitan al menos 3 slots para el test"

    target = slots_before[2]
    response = await client.post("/api/v1/appointments/", json={
        "customer_full_name": "Cliente Test",
        "customer_phone": "55555555",
        "service_id": service_id,
        "start_time": target,
    })
    assert response.status_code == 201, response.text

    slots_after = await get_slots(client, day, service_id)

    assert target not in slots_after, (
        f"El slot reservado {target} sigue ofreciéndose como libre"
    )
    assert slots_after == [s for s in slots_before if s != target], (
        "La grilla cambió más allá del slot reservado: "
        f"antes={slots_before} despues={slots_after}"
    )


async def test_available_slots_devuelve_instantes_con_offset(client):
    """El contrato es ISO-8601 con offset, no un 'HH:MM' ambiguo."""
    day = next_open_day()
    service_id = await create_service(client)
    slots = await get_slots(client, day, service_id)

    assert slots
    for slot in slots:
        parsed = datetime.fromisoformat(slot)
        assert parsed.tzinfo is not None, f"{slot} no trae offset de zona horaria"
        assert parsed.date() == day, f"{slot} no cae en el día pedido ({day})"


# ----------------------------------------------------------------------
# REGRESION: validación de entrada
# ----------------------------------------------------------------------
async def test_start_time_naive_es_rechazado_422(client):
    """Un datetime sin offset es ambiguo: 422, no un 500 por TypeError."""
    day = next_open_day()
    service_id = await create_service(client)

    response = await client.post("/api/v1/appointments/", json={
        "customer_full_name": "Cliente Test",
        "customer_phone": "66666666",
        "service_id": service_id,
        "start_time": f"{day.isoformat()}T10:00:00",  # sin offset
    })
    assert response.status_code == 422, response.text


async def test_service_id_malformado_devuelve_422_no_500(client):
    """Un UUID inválido se rechaza en el borde (422), no en el driver (500)."""
    day = next_open_day()
    response = await client.get(
        "/api/v1/appointments/available-slots",
        params={"date": day.isoformat(), "service_id": "no-es-un-uuid"},
    )
    assert response.status_code == 422, response.text


async def test_fecha_malformada_devuelve_422(client):
    service_id = await create_service(client)
    response = await client.get(
        "/api/v1/appointments/available-slots",
        params={"date": "10/10/2026", "service_id": service_id},
    )
    assert response.status_code == 422, response.text


# ----------------------------------------------------------------------
# REGRESION: soft delete de servicios
# ----------------------------------------------------------------------
async def test_delete_de_servicio_con_turnos_es_soft_delete(client):
    """Borrar un servicio en uso NO debe romper ni destruir el historial."""
    day = next_open_day()
    service_id = await create_service(client)

    response = await book(client, day, 10, 0, service_id, "77777777")
    assert response.status_code == 201, response.text
    appointment_id = response.json()["id"]

    delete_response = await client.delete(f"/api/v1/services/{service_id}")
    assert delete_response.status_code == 200, delete_response.text

    # El servicio sigue existiendo (la cita lo referencia) pero inactivo.
    active = await client.get("/api/v1/services/", params={"only_active": True})
    assert service_id not in [s["id"] for s in active.json()]

    all_services = await client.get("/api/v1/services/")
    assert service_id in [s["id"] for s in all_services.json()]

    # El turno histórico sigue siendo legible y conserva su precio.
    appointments = await client.get("/api/v1/appointments/")
    assert appointments.status_code == 200
    stored = [a for a in appointments.json() if a["id"] == appointment_id]
    assert len(stored) == 1
    assert stored[0]["price_at_booking"] == "1000.00"


async def test_no_se_puede_reservar_un_servicio_desactivado(client):
    day = next_open_day()
    service_id = await create_service(client)
    assert (await client.delete(f"/api/v1/services/{service_id}")).status_code == 200

    response = await book(client, day, 10, 0, service_id, "88888888")
    assert response.status_code == 404

    slots = await client.get(
        "/api/v1/appointments/available-slots",
        params={"date": day.isoformat(), "service_id": service_id},
    )
    assert slots.status_code == 404


# ----------------------------------------------------------------------
# REGRESION: configuración comercial
# ----------------------------------------------------------------------
async def test_settings_rechaza_rango_invertido(client):
    response = await client.put(
        "/api/v1/settings/", json={"open_hour": 20, "close_hour": 9}
    )
    assert response.status_code == 422, response.text


async def test_settings_rechaza_hora_fuera_de_rango(client):
    response = await client.put("/api/v1/settings/", json={"open_hour": 25})
    assert response.status_code == 422, response.text


async def test_settings_rechaza_update_parcial_que_invierte_el_rango(client):
    """Mandar solo open_hour debe validarse contra el close_hour ya guardado."""
    assert (
        await client.put("/api/v1/settings/", json={"open_hour": 9, "close_hour": 18})
    ).status_code == 200

    response = await client.put("/api/v1/settings/", json={"open_hour": 22})
    assert response.status_code == 400, response.text


async def test_work_days_csv_corrupto_no_vacia_la_agenda(client):
    """Un CSV sin días válidos no debe dejar el negocio sin atención."""
    assert (
        await client.put("/api/v1/settings/", json={"work_days_csv": "abc"})
    ).status_code == 422

    # Un CSV válido que excluye el día pedido sí debe devolver grilla vacía.
    assert (
        await client.put("/api/v1/settings/", json={"work_days_csv": "0"})
    ).status_code == 200

    await create_service(client)
    monday = next_open_day()
    while monday.weekday() != 0:
        monday += timedelta(days=1)

    services = (await client.get("/api/v1/services/")).json()
    slots = await get_slots(client, monday, services[0]["id"])
    assert slots, "El lunes está en work_days_csv='0', debería tener grilla"


async def test_get_settings_no_persiste_filas(client):
    """Un GET no debe tener efectos secundarios (no crea configuración)."""
    from sqlalchemy import func, select

    from app.models.all_models import BusinessSettings
    from conftest import TestingSessionLocal

    response = await client.get("/api/v1/settings/")
    assert response.status_code == 200
    assert response.json()["open_hour"] == DEFAULT_OPEN_HOUR

    async with TestingSessionLocal() as session:
        total = (
            await session.execute(
                select(func.count()).select_from(BusinessSettings)
            )
        ).scalar_one()

    assert total == 0, "GET /settings/ persistió una fila (efecto secundario)"
