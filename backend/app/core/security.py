# app/core/security.py
from passlib.context import CryptContext

# Configuramos explícitamente bcrypt como nuestro esquema de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con el hash guardado."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera un hash seguro a partir de una contraseña en texto plano."""
    return pwd_context.hash(password)
