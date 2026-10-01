from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None
    expires_in: int | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyResetCodeRequest(BaseModel):
    email: str
    code: str = Field(
        min_length=6,
        max_length=6
    )


class ResetPasswordRequest(BaseModel):
    email: str

    code: str = Field(
        min_length=6,
        max_length=6
    )

    new_password: str = Field(
        min_length=6
    )
