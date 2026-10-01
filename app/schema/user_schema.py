from datetime import datetime

from pydantic import BaseModel

from app.schema.base_schema import MongoModel


class UserCreate(BaseModel):

    username: str
    password: str
    role: str
    email : str
    status: bool = True


class UserUpdate(BaseModel):

    username: str | None = None
    password: str | None = None
    role: str | None = None
    email : str | None = None
    status: bool | None = None


class UserResponse(MongoModel):

    username: str
    role: str
    email : str
    created_at: datetime
    status: bool