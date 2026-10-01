from datetime import timedelta
from uuid import uuid4

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.config.settings import settings
from app.utils.dateZone import DateUtils
from app.utils.exceptions import UnauthorizedException


ALGORITHM = "HS256"


def _create_token(data: dict, expires_delta: timedelta, token_type: str):
    now = DateUtils.now_argentina()

    to_encode = data.copy()
    to_encode["iat"] = now
    to_encode["exp"] = now + expires_delta
    to_encode["jti"] = str(uuid4())
    to_encode["type"] = token_type

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_access_token(data, expires_delta: timedelta):
    """Crea un access token JWT."""
    return _create_token(
        data,
        expires_delta,
        "access",
    )


def create_refresh_token(user_id: str, expires_delta: timedelta):
    """Crea un refresh token sin datos sensibles ni permisos."""
    return _create_token(
        {
            "sub": str(user_id),
        },
        expires_delta,
        "refresh",
    )


def _decode_token(token: str, expected_type: str | None = None):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        token_type = payload.get("type")

        # Los tokens emitidos antes de esta versión no tenían type.
        # Se aceptan como access tokens hasta que expiren para evitar
        # invalidar sesiones existentes de forma innecesaria.
        if expected_type == "access":
            if token_type not in (None, "access"):
                raise UnauthorizedException("Tipo de token inválido")

        elif expected_type == "refresh":
            if token_type != "refresh":
                raise UnauthorizedException("Refresh token inválido")

        return payload

    except ExpiredSignatureError:
        raise UnauthorizedException("Token expirado")

    except UnauthorizedException:
        raise

    except InvalidTokenError:
        raise UnauthorizedException("Token inválido")


def decode_access_token(token):
    return _decode_token(token, "access")


def decode_refresh_token(token):
    return _decode_token(token, "refresh")
