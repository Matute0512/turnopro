# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.repositories.user import user_repo
from app.models.all_models import User

# Le indicamos a Swagger cuál es la ruta para hacer el login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependencia que extrae el token del header 'Authorization: Bearer <token>',
    verifica su firma criptográfica y devuelve el usuario autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o el token expiró",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        # Decodificamos el JWT usando nuestra clave secreta
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        # Si el token fue modificado maliciosamente o expiró, cae aquí
        raise credentials_exception

    # Verificamos que el usuario aún exista en la base de datos
    user = await user_repo.get_by_id(db, id=user_id)
    if user is None:
        raise credentials_exception

    return user
