from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schema.base_schema import MongoModel


CashRegisterShift = Literal[
    "morning",
    "night"
]

CashRegisterStatus = Literal[
    "open",
    "close"
]

class CashRegisterCreate(BaseModel):

    date: str

    shift: CashRegisterShift

    opened_at: datetime

    opening_amount: float

    status_cash_register: CashRegisterStatus = "open"

    status: bool = True


class CashRegisterUpdate(BaseModel):

    shift: CashRegisterShift | None = None

    opened_at: datetime | None = None

    opening_amount: float | None = None

    closed_at: datetime | None = None

    closing_amount: float | None = None

    status_cash_register: CashRegisterStatus | None = None

    status: bool | None = None
class CashRegisterResponse(
    CashRegisterCreate,
    MongoModel
):

    opened_by_user_id: str | None = None

    closed_by_user_id: str | None = None

    updated_by_user_id: str | None = None

    sales_total: float | None = None

    sales_cash: float | None = None

    sales_transfer: float | None = None

    sales_qr: float | None = None

    sales_debit_card: float | None = None

    manual_income: float | None = None

    manual_expense: float | None = None

    manual_income_cash: float | None = None

    manual_expense_cash: float | None = None

    closed_at: datetime | None = None

    closing_amount: float | None = None

    expected_amount: float | None = None

    difference: float | None = None