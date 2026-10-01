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
    UnauthorizedException
)


class PasswordResetService:

    def __init__(self):

        self.repository = PasswordResetRepository()
        self.user_repository = UserRepository()
        self.email_service = EmailService()

    async def create_reset_code(self, email):

        user = await self.user_repository.get_by_email(
            email
        )

        # No revelamos si el usuario existe.
        if not user:
            return

        if not user["status"]:
            return

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
            raise UnauthorizedException(
                "Código inválido o expirado."
            )

        reset = await self.repository.get_by_user_id(
            user["id"]
        )

        if not reset:
            raise UnauthorizedException(
                "Código inválido o expirado."
            )

        now = DateUtils.now_argentina()

        if reset["expires_at"] <= now:

            raise UnauthorizedException(
                "Código inválido o expirado."
            )

        if not verify_password(
            code,
            reset["code_hash"]
        ):

            raise UnauthorizedException(
                "Código inválido o expirado."
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
            raise UnauthorizedException(
                "Código inválido o expirado."
            )

        reset = await self.repository.get_by_user_id(
            user["id"]
        )

        if not reset:
            raise UnauthorizedException(
                "Código inválido o expirado."
            )

        now = DateUtils.now_argentina()

        if reset["expires_at"] <= now:

            raise UnauthorizedException(
                "Código inválido o expirado."
            )

        if not verify_password(
            code,
            reset["code_hash"]
        ):

            raise UnauthorizedException(
                "Código inválido o expirado."
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