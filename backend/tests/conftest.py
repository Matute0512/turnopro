# backend/tests/conftest.py
import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.api.deps import get_current_user
from app.models.all_models import User

# 1. Base de datos SQLite asíncrona en RAM (desaparece al terminar los tests)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

# 2. Reemplazamos la conexión real a PostgreSQL por nuestra SQLite


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# 3. Reemplazamos la autenticación para no tener que hacer login en cada test


async def override_get_current_user():
    return User(id=uuid.uuid4(), email="tester@turnopro.com")

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# 4. Fixture que crea las tablas antes de cada test y las borra al terminar


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 5. Cliente HTTP asíncrono para simular peticiones a la API


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
