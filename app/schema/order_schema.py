from datetime import datetime

from pydantic import BaseModel

from app.schema.base_schema import MongoModel
from app.schema.order_item_schema import OrderItemLoad, OrderItemResponse
from app.schema.payment_schema import PaymentMethod, PaymentStatus


class OrderCreate(BaseModel):

    order_number: int
    customer_name: str
    items: list[OrderItemLoad]
    method_payment: PaymentMethod
    status_payment: PaymentStatus
    delivery_time: str
    cash_register_id: str | None = None
    status: bool = True


class OrderUpdate(BaseModel):

    order_number: int | None = None
    customer_name: str | None = None
    items: list[OrderItemLoad] | None = None
    method_payment: PaymentMethod | None = None
    status_payment: PaymentStatus | None = None
    delivery_time: str | None = None
    cash_register_id: str | None = None
    status: bool | None = None


class OrderResponse(MongoModel):

    order_number: int
    customer_name: str
    items: list[OrderItemResponse]
    method_payment: PaymentMethod
    status_payment: PaymentStatus
    delivery_time: str
    cash_register_id: str | None = None
    status: bool = True
    total_price: float
    created_at: datetime
