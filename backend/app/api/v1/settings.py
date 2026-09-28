# app/api/v1/settings.py
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.all_schemas import BusinessSettingsUpdate, BusinessSettingsResponse
from app.repositories.base import BaseRepository
from app.models.all_models import BusinessSettings, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])
settings_repo = BaseRepository(BusinessSettings)

DEFAULT_WORK_DAYS_CSV = "0,1,2,3,4,5"
DEFAULT_OPEN_HOUR = 9
DEFAULT_CLOSE_HOUR = 20


@router.get("/", response_model=BusinessSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la configuración comercial.

    NO persiste nada: un GET no debe tener efectos secundarios (rompe cachés y
    crea filas duplicadas si entran dos requests concurrentes en un local que
    todavía no tiene configuración). Si no existe, se devuelven los defaults.
    """
    settings_list = await settings_repo.get_multi(
        db, limit=1, order_by=BusinessSettings.open_hour
    )
    if settings_list:
        return settings_list[0]

    return BusinessSettingsResponse(
        id=uuid4(),
        work_days_csv=DEFAULT_WORK_DAYS_CSV,
        open_hour=DEFAULT_OPEN_HOUR,
        close_hour=DEFAULT_CLOSE_HOUR,
    )


@router.put("/", response_model=BusinessSettingsResponse)
async def update_settings(
    settings_in: BusinessSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza la configuración comercial (solo Admin)."""
    settings_list = await settings_repo.get_multi(
        db, limit=1, order_by=BusinessSettings.open_hour
    )
    if settings_list:
        db_settings = settings_list[0]
    else:
        db_settings = await settings_repo.create(db, {})

    update_data = settings_in.model_dump(exclude_unset=True)

    # Un update PARCIAL puede romper el rango aunque cada campo sea válido por
    # separado (ej. mandar solo open_hour=22 con close_hour=20 ya guardado).
    # Validamos contra el estado FINAL resultante, no contra el payload.
    final_open = update_data.get("open_hour", db_settings.open_hour)
    final_close = update_data.get("close_hour", db_settings.close_hour)
    if final_open >= final_close:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"open_hour ({final_open}) debe ser menor que "
                f"close_hour ({final_close})."
            ),
        )

    return await settings_repo.update(db, db_obj=db_settings, obj_in=update_data)
