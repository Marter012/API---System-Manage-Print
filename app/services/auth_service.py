from datetime import timedelta

from app.repositories.user_repository import UserRepository

from app.services.password_reset_service import PasswordResetService

from app.utils.exceptions import UnauthorizedException, NotFoundException

from app.utils.password import verify_password

from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)


class AuthService:

    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    def __init__(self):

        self.repository = UserRepository()

        self.password_reset_service = (
            PasswordResetService()
        )

    async def _get_active_user_by_id(self, user_id):
        try:
            user = await self.repository.get_by_id(user_id)
        except NotFoundException:
            raise UnauthorizedException(
                "Usuario inactivo o inexistente"
            )

        if not user or not user.get("status", False):
            raise UnauthorizedException(
                "Usuario inactivo o inexistente"
            )

        return user

    def _build_tokens(self, user):
        user_claims = {
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
        }

        access_token = create_access_token(
            user_claims,
            timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        refresh_token = create_refresh_token(
            user["id"],
            timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def login(
        self,
        username,
        password
    ):

        existing_user = await self.repository.get_by_username(
            username
        )

        if not existing_user:
            raise UnauthorizedException(
                "Usuario o contraseña incorrectos."
            )

        if not existing_user["status"]:
            raise UnauthorizedException(
                "Usuario o contraseña incorrectos."
            )

        if not verify_password(
            password,
            existing_user["password_hash"]
        ):
            raise UnauthorizedException(
                "Usuario o contraseña incorrectos."
            )

        return self._build_tokens(existing_user)

    async def refresh(self, refresh_token):
        payload = decode_refresh_token(refresh_token)

        user_id = payload.get("sub")

        if not user_id:
            raise UnauthorizedException("Refresh token inválido")

        user = await self._get_active_user_by_id(user_id)

        return self._build_tokens(user)

    async def forgot_password(self, email):

        await self.password_reset_service.create_reset_code(
            email
        )

        return {
            "message": (
                "Si el email corresponde a una cuenta, "
                "recibirás un código de recuperación."
            )
        }

    async def verify_reset_code(
        self,
        email,
        code
    ):

        await self.password_reset_service.verify_code(
            email,
            code
        )

        return {
            "message": "Código válido."
        }

    async def reset_password(
        self,
        email,
        code,
        new_password
    ):

        await self.password_reset_service.reset_password(
            email,
            code,
            new_password
        )

        return {
            "message": "Contraseña actualizada correctamente."
        }
