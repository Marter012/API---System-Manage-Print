from datetime import datetime

from pydantic import BaseModel

from app.schema.base_schema import MongoModel

from app.schema.payment_schema import (
    PaymentMethod,
    CashMovementType
)


class CashMovementCreate(BaseModel):

    cash_register_id: str

    order_id: str | None = None

    type: CashMovementType

    category: str

    amount: float

    method_payment: PaymentMethod

    description: str

    date: datetime

    status: bool = True


class CashMovementUpdate(BaseModel):

    cash_register_id: str | None = None

    order_id: str | None = None

    type: CashMovementType | None = None

    category: str | None = None

    amount: float | None = None

    method_payment: PaymentMethod | None = None

    description: str | None = None

    date: datetime | None = None

    status: bool | None = None


class CashMovementResponse(
    CashMovementCreate,
    MongoModel
):

    pass