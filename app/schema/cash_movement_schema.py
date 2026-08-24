from pydantic import BaseModel

from datetime import datetime


class CashMovementCreate(BaseModel):

    cash_register_id: str

    # Orden relacionada, si corresponde
    order_id: str | None = None

    # inflow / outflow
    type: str

    # sale / expense / withdrawal / refund...
    category: str

    amount: float

    method_payment: str

    description: str

    date: datetime

    status: bool = True


class CashMovementUpdate(BaseModel):

    cash_register_id: str | None = None

    order_id: str | None = None

    type: str | None = None

    category: str | None = None

    amount: float | None = None

    method_payment: str | None = None

    description: str | None = None

    date: datetime | None = None

    status: bool | None = None


class CashMovementResponse(BaseModel):

    id: str

    cash_register_id: str

    order_id: str | None = None

    type: str

    category: str

    amount: float

    method_payment: str

    description: str

    date: datetime

    status: bool