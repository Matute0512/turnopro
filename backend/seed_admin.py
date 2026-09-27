# seed_admin.py
import asyncio
from app.core.database import AsyncSessionLocal
from app.repositories.user import user_repo
from app.core.security import get_password_hash


async def create_first_admin():
    async with AsyncSessionLocal() as db:
        # Verifica si ya existe
        exists = await user_repo.get_by_email(db, "admin@turnopro.com")
        if exists:
            print("El admin ya existe.")
            return

        # Creamos el usuario con la contraseña hasheada
        admin_data = {
            "email": "admin@turnopro.com",
            "password_hash": get_password_hash("Admin1234!")
        }
        await user_repo.create(db, admin_data)
        print("Administrador creado exitosamente: admin@turnopro.com / Admin1234!")

if __name__ == "__main__":
    asyncio.run(create_first_admin())
