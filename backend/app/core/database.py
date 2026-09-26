# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# engine: Maneja el pool de conexiones a PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Usamos async_sessionmaker (Específico para SQLAlchemy 2.0+)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base: Clase de la que heredarán todos nuestros modelos (tablas)
Base = declarative_base()


async def get_db():
    """
    Dependencia que provee una sesión asíncrona de base de datos
    por cada petición web y la cierra automáticamente al terminar.
    """
    async with AsyncSessionLocal() as session:
        yield session
