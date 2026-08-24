from pydantic import BaseModel

from datetime import datetime

from app.schema.base_schema import MongoModel


class CashRegisterCreate(BaseModel):

    opened_at: datetime

    opening_amount: float

    status_cash_register: str = "open"

    status: bool = True


class CashRegisterUpdate(BaseModel):

    opened_at: datetime | None = None

    opening_amount: float | None = None

    closed_at: datetime | None = None

    closing_amount: float | None = None

    status_cash_register: str | None = None

    status: bool | None = None


class CashRegisterResponse(
    CashRegisterCreate,
    MongoModel
):

    closed_at: datetime | None = None

    closing_amount: float | None = None

    expected_amount: float | None = None

    difference: float | None = None

    status_cash_register: str

    status: bool