from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.schemas.all_schemas import BusinessSettingsUpdate, BusinessSettingsResponse
from app.repositories.base import BaseRepository
from app.models.all_models import BusinessSettings, User
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])
settings_repo = BaseRepository(BusinessSettings)


@router.get("/", response_model=BusinessSettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Obtiene la configuración comercial. Crea una por defecto si no existe."""
    settings_list = await settings_repo.get_all(db)
    if not settings_list:
        # Default config: Lun-Vie (0,1,2,3,4) y Sab(5), Dom(6) dependiendo del default
        # En el modelo pusimos "0,1,2,3,4,5" como default (Lun a Sab)
        return await settings_repo.create(db, {})
    return settings_list[0]


@router.put("/", response_model=BusinessSettingsResponse)
async def update_settings(
    settings_in: BusinessSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualiza la configuración comercial (solo Admin)."""
    settings_list = await settings_repo.get_all(db)
    if not settings_list:
        db_settings = await settings_repo.create(db, {})
    else:
        db_settings = settings_list[0]

    update_data = settings_in.model_dump(exclude_unset=True)
    return await settings_repo.update(db, db_obj=db_settings, obj_in=update_data)
