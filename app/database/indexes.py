from app.database.connection import (
    users_collection,
    password_reset_collection,
    cash_register_collection,
    cash_movement_collection,
)


async def create_indexes():

    await users_collection.create_index(
        "username",
        unique=True
    )

    await users_collection.create_index(
        "email",
        unique=True
    )

    await password_reset_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
    )

    # Índices para las consultas de auditoría de caja.
    await cash_register_collection.create_index(
        "opened_by_user_id"
    )

    await cash_register_collection.create_index(
        "closed_by_user_id"
    )

    await cash_movement_collection.create_index(
        "user_id"
    )

    await cash_movement_collection.create_index(
        "updated_by_user_id"
    )
