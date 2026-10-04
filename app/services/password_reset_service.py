import secrets

from datetime import timedelta

from app.repositories.password_reset_repository import (
    PasswordResetRepository
)

from app.repositories.user_repository import (
    UserRepository
)

from app.services.email_service import EmailService

from app.utils.password import (
    hash_password,
    verify_password
)

from app.utils.dateZone import DateUtils

from app.utils.exceptions import (
    UnauthorizedException,
    NotFoundException
)


class PasswordResetService:

    def __init__(self):

        self.repository = PasswordResetRepository()
        self.user_repository = UserRepository()
        self.email_service = EmailService()


    async def create_reset_code(
        self,
        email
    ):

        user = await self.user_repository.get_by_email(
            email
        )

        if not user:

            raise NotFoundException(
                "No existe un usuario registrado con ese email."
            )

        if not user.get("status", False):

            raise UnauthorizedException(
                "El usuario asociado a ese email se encuentra inactivo."
            )

        await self.repository.invalidate_by_user_id(
            user["id"]
        )

        code = f"{secrets.randbelow(1000000):06d}"

        code_hash = hash_password(
            code
        )

        now = DateUtils.now_argentina()

        expires_at = (
            now
            + timedelta(minutes=10)
        )

        reset_data = {
            "user_id": user["id"],
            "code_hash": code_hash,
            "expires_at": expires_at,
            "used": False,
            "status": "pending",
            "created_at": now
        }

        await self.repository.create(
            reset_data
        )

        await self.email_service.send_password_reset_code(
            user["email"],
            code
        )


    async def verify_code(
        self,
        email,
        code
    ):

        user = await self.user_repository.get_by_email(
            email
        )

        if not user:

            raise NotFoundException(
                "No existe un usuario registrado con ese email."
            )

        if not user.get("status", False):

            raise UnauthorizedException(
                "El usuario asociado a ese email se encuentra inactivo."
            )

        reset = await self.repository.get_by_user_id(
            user["id"]
        )

        if not reset:

            raise UnauthorizedException(
                "No existe un código de recuperación válido para este usuario."
            )

        if reset.get("used", False):

            raise UnauthorizedException(
                "El código de recuperación ya fue utilizado."
            )

        if reset.get("status") == "verified":

            raise UnauthorizedException(
                "El código de recuperación ya fue verificado."
            )

        now = DateUtils.now_argentina()

        if reset["expires_at"] <= now:

            raise UnauthorizedException(
                "El código de recuperación ha expirado."
            )

        if not verify_password(
            code,
            reset["code_hash"]
        ):

            raise UnauthorizedException(
                "El código de recuperación ingresado es incorrecto."
            )

        await self.repository.mark_as_verified(
            reset["id"]
        )

        return True


    async def reset_password(
        self,
        email,
        code,
        new_password
    ):

        user = await self.user_repository.get_by_email(
            email
        )

        if not user:

            raise NotFoundException(
                "No existe un usuario registrado con ese email."
            )

        if not user.get("status", False):

            raise UnauthorizedException(
                "El usuario asociado a ese email se encuentra inactivo."
            )

        reset = await self.repository.get_by_user_id(
            user["id"]
        )

        if not reset:

            raise UnauthorizedException(
                "No existe un proceso de recuperación válido para este usuario."
            )

        if reset.get("used", False):

            raise UnauthorizedException(
                "El proceso de recuperación ya fue completado."
            )

        if reset.get("status") != "verified":

            raise UnauthorizedException(
                "El código de recuperación todavía no fue verificado."
            )

        now = DateUtils.now_argentina()

        if reset["expires_at"] <= now:

            raise UnauthorizedException(
                "El código de recuperación ha expirado."
            )

        if not verify_password(
            code,
            reset["code_hash"]
        ):

            raise UnauthorizedException(
                "El código de recuperación ingresado es incorrecto."
            )

        password_hash = hash_password(
            new_password
        )

        await self.user_repository.update(
            user["id"],
            {
                "password_hash": password_hash
            }
        )

        await self.repository.mark_as_used(
            reset["id"]
        )

        return True


    async def get_reset_status(
        self,
        email
    ):

        user = await self.user_repository.get_by_email(
            email
        )

        if not user:

            raise NotFoundException(
                "No existe un usuario registrado con ese email."
            )

        reset = await self.repository.get_status_by_user_id(
            user["id"]
        )

        if not reset:

            return {
                "status": "none"
            }

        if reset.get("status") == "pending":

            if reset["expires_at"] <= DateUtils.now_argentina():

                return {
                    "status": "expired"
                }

        return {
            "status": reset.get(
                "status",
                "none"
            )
        }