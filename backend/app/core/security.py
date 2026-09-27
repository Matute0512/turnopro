# app/core/security.py
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con el hash guardado."""
    # bcrypt requiere que los strings sean convertidos a bytes
    return bcrypt.checkpw(
        password=plain_password.encode('utf-8'),
        hashed_password=hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Genera un hash seguro Bcrypt a partir de una contraseña en texto plano."""
    # Generamos un salt seguro y creamos el hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Lo decodificamos a string para guardarlo en la base de datos (PostgreSQL)
    return hashed.decode('utf-8')


def create_access_token(data: dict) -> str:
    """Crea un JWT de corta vida para autorizar peticiones HTTP."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Crea un JWT de larga vida que viajará exclusivamente en una Cookie HttpOnly."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(days=7)  # 7 días de duración
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
