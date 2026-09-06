from datetime import datetime

from pydantic import BaseModel

from app.schema.order_item_schema import OrderItemLoad
from app.schema.base_schema import MongoModel


PAYMENT_PENDING = "pending"
PAYMENT_PAID = "paid"
PAYMENT_CANCELLED = "cancelled"


VALID_PAYMENT_STATUS = [
    PAYMENT_PENDING,
    PAYMENT_PAID,
    PAYMENT_CANCELLED
]


class OrderCreate(BaseModel):

    order_number: int

    customer_name: str

    items: list[OrderItemLoad]

    method_payment: str

    status_payment: str

    delivery_time: str

    status: bool = True


class OrderUpdate(BaseModel):

    order_number: int | None = None

    customer_name: str | None = None

    items: list[OrderItemLoad] | None = None

    method_payment: str | None = None

    status_payment: str | None = None

    delivery_time: str | None = None

    status: bool | None = None


class OrderResponse(
    OrderCreate,
    MongoModel
):

    total_price: float

    created_at: datetime