# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user import user_repo
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.models.all_models import AuditLog

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para iniciar sesión.
    Devuelve el Access Token en el JSON y el Refresh Token en una Cookie HttpOnly.
    """
    # 1. Buscar usuario (El estándar OAuth2 usa el campo 'username' para el email)
    user = await user_repo.get_by_email(db, email=form_data.username)

    # 2. Verificación de credenciales (Zero Trust)
    if not user or not verify_password(form_data.password, user.password_hash):
        # NOTA: En un sistema en producción estricto, aquí también registraríamos el LOGIN_FAILED
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generar Token (Guardamos el ID del usuario como 'subject' del token)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # 4. Configurar la Cookie HttpOnly para el Refresh Token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # TODO: Cambiar a True en producción (cuando tengamos HTTPS)
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 días de duración en segundos
    )

    # 5. Registro de Auditoria (Trazabilidad de seguridad)
    # Extraemos la IP del request de FastAPI
    client_ip = request.client.host if request.client else "Unknown"

    audit_log = AuditLog(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        ip_address=client_ip
    )
    db.add(audit_log)
    await db.commit()

    # 6. Devolver el Access Token al cliente (Frontend)7
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
