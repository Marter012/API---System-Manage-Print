from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService
from app.utils.password import hash_password
from app.utils.exceptions import ConflictException
from app.utils.dateZone import DateUtils


class UserService(BaseService):

    def __init__(self):
        super().__init__(UserRepository())

    async def create(self, data):

        existing_username = await self.repository.get_by_username(
            data.username
        )
        

        if existing_username:
            raise ConflictException(
                "Nombre de usuario ya existente."
            )
        
        existing_email = await self.repository.get_by_email(
            data.email
        )
        
        
        if existing_email:
            raise ConflictException(
                "Email ya se encuentra asociado a un cliente."
            ) 

        password_hash = hash_password(
            data.password
        )

        user_data = {
            "username": data.username,
            "password_hash": password_hash,
            "role": data.role,
            "email" : data.email,
            "status": data.status,
            "created_at": DateUtils.now_argentina()
        }

        return await self.repository.create(
            user_data
        )

    async def update(self, document_id, data):

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        if "username" in update_data:

            existing_username = await self.repository.get_by_username(
                update_data["username"]
            )

            if (
                existing_username
                and existing_username["id"] != document_id
            ):
                raise ConflictException(
                    "Nombre de usuario ya existente."
                )

        if "email" in update_data:

            existing_email = await self.repository.get_by_email(
                update_data["email"]
            )

            if (
                existing_email
                and existing_email["id"] != document_id
            ):
                raise ConflictException(
                    "Email ya se encuentra asociado a un cliente."
                )

        if "password" in update_data:

            update_data["password_hash"] = hash_password(
                update_data["password"]
            )

            del update_data["password"]

        return await self.repository.update(
            document_id,
            update_data
        )