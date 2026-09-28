# backend/tests/test_appointments.py
import pytest

# Le decimos a pytest que estas pruebas usan asyncio
pytestmark = pytest.mark.asyncio


async def test_appointment_overlap_prevention(client):
    """
    Prueba End-to-End simulada:
    1. Crea un servicio de 30 min.
    2. Agenda un turno a las 10:00 (Exitoso).
    3. Intenta agendar a las 10:15 (Debe fallar - Conflicto 409).
    4. Intenta agendar a las 10:30 (Exitoso - Empieza al terminar el anterior).
    """

    # PASO 1: Inyectar un servicio en la base de datos aislada
    service_response = await client.post("/api/v1/services/", json={
        "name": "Corte Test",
        "duration_minutes": 30,
        "price": 1000
    })
    assert service_response.status_code == 201
    service_id = service_response.json()["id"]

    # PASO 2: Agendar el primer turno (10:00 AM)
    appointment_1 = {
        "customer_full_name": "Cliente Uno",
        "customer_phone": "11111111",
        "service_id": service_id,
        "start_time": "2026-10-10T10:00:00Z"
    }
    res_1 = await client.post("/api/v1/appointments/", json=appointment_1)
    assert res_1.status_code == 201  # HTTP 201: Created

    # PASO 3: Intentar pisar el turno (10:15 AM) - DEBE FALLAR
    appointment_2_overlap = {
        "customer_full_name": "Cliente Dos",
        "customer_phone": "22222222",
        "service_id": service_id,
        "start_time": "2026-10-10T10:15:00Z"
    }
    res_2 = await client.post("/api/v1/appointments/", json=appointment_2_overlap)
    assert res_2.status_code == 409  # HTTP 409: Conflict

    # PASO 4: Agendar justo al terminar el primero (10:30 AM) - DEBE PASAR
    appointment_3_adjacent = {
        "customer_full_name": "Cliente Tres",
        "customer_phone": "33333333",
        "service_id": service_id,
        "start_time": "2026-10-10T10:30:00Z"
    }
    res_3 = await client.post("/api/v1/appointments/", json=appointment_3_adjacent)
    assert res_3.status_code == 201
