from datetime import datetime

from pydantic import BaseModel


class PasswordResetCreate(BaseModel):
    user_id: str
    code_hash: str
    expires_at: datetime
    used: bool = False
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyResetCodeRequest(BaseModel):
    email: str
    code: str


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str