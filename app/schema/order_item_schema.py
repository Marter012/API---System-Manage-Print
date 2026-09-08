from pydantic import BaseModel
from app.schema.base_schema import MongoModel


class OrderItemLoad(BaseModel):

    product_id: str

    quantity: int


class OrderItemCreate(BaseModel):

    product_id: str

    name: str

    quantity: int

    unit_price: float

    subtotal: float

    status: bool = True


class OrderItemUpdate(BaseModel):

    product_id: str | None = None

    name: str | None = None

    quantity: int | None = None

    unit_price: float | None = None

    subtotal: float | None = None

    status: bool | None = None


class OrderItemResponse(
    OrderItemCreate,MongoModel
):
    pass