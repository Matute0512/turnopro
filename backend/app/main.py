# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos nuestros enrutadores
from app.api.v1.appointments import router as appointments_router
from app.api.v1.services import router as services_router
from app.api.v1.auth import router as auth_router
from app.api.v1.customers import router as customers_router
from app.api.v1.settings import router as settings_router

app = FastAPI(
    title="TurnoPro API",
    description="API de gestión de turnos para MVP (Portafolio)",
    version="1.0.0"
)

# Configuración CORS (Cross-Origin Resource Sharing)
# Crítico para la Fase 6: Permite que el frontend en Flutter/React se comunique con esta API.
app.add_middleware(
    CORSMiddleware,
    # En producción cambiaremos esto por el dominio real (ej. "https://turnopro.com")
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos las rutas en la aplicacion principal
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint básico para monitoreo de uptime en producción."""
    return {"status": "ok", "message": "TurnoPro API corriendo exitosamente"}
