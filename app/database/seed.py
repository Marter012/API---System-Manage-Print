from app.database.connection import users_collection
from app.utils.password import hash_password
from app.utils.dateZone import DateUtils
from app.config.settings import settings


async def create_initial_admin():

    users_count = await users_collection.count_documents({})

    if users_count > 0:
        return

    password_hash = hash_password(
        settings.INITIAL_ADMIN_PASSWORD
    )

    admin_data = {
        "username": settings.INITIAL_ADMIN_USERNAME,
        "email": settings.INITIAL_ADMIN_EMAIL,
        "password_hash": password_hash,
        "role": "admin",
        "created_at": DateUtils.now_argentina(),
        "status": True
    }

    await users_collection.insert_one(admin_data)

    print(
        f"Usuario administrador inicial creado: "
        f"{settings.INITIAL_ADMIN_USERNAME}"
    )