from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user

from app.schema.auth_schema import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    VerifyResetCodeRequest,
    ResetPasswordRequest,
)

from app.schema.user_schema import UserResponse

from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


service = AuthService()


@router.post(
    "/",
    response_model=TokenResponse
)
async def login(
    user: LoginRequest
):

    return await service.login(
        user.username,
        user.password
    )


@router.post(
    "/refresh",
    response_model=TokenResponse
)
async def refresh(
    data: RefreshTokenRequest
):

    return await service.refresh(
        data.refresh_token
    )


@router.get(
    "/me",
    response_model=UserResponse
)
async def get_me(
    current_user=Depends(get_current_user)
):

    return await service.repository.get_by_id(
        current_user["sub"]
    )


@router.post(
    "/forgot-password"
)
async def forgot_password(
    data: ForgotPasswordRequest
):

    return await service.forgot_password(
        data.email
    )


@router.post(
    "/verify-reset-code"
)
async def verify_reset_code(
    data: VerifyResetCodeRequest
):

    return await service.verify_reset_code(
        data.email,
        data.code
    )


@router.post(
    "/reset-password"
)
async def reset_password(
    data: ResetPasswordRequest
):

    return await service.reset_password(
        data.email,
        data.code,
        data.new_password
    )

@router.get(
    "/reset-status"
)
async def reset_status(
    email: str,
):

    return await service.get_reset_status(
        email,
    )