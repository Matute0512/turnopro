# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Zona horaria del local. Es la referencia de TODAS las reglas comerciales
    # (días de atención, apertura/cierre, grilla de turnos). En la base de datos
    # se persiste siempre en UTC; la conversión ocurre en la capa de servicios.
    BUSINESS_TIMEZONE: str = "America/Argentina/Buenos_Aires"

    # Le decimos que lea desde el archivo .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


settings = Settings()
