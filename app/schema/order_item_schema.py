from typing import Literal

from pydantic import BaseModel, Field
from app.schema.base_schema import MongoModel


class PromotionSelectionLoad(BaseModel):
    """Selección concreta realizada para un grupo de la promoción."""

    promotion_item_id: str
    product_id: str
    quantity: int = Field(gt=0)


class PromotionSelectionResponse(PromotionSelectionLoad):

    group_name: str
    product_name: str


class OrderItemLoad(BaseModel):

    # Backward compatible: si el frontend no envía item_type,
    # el item se interpreta como producto normal.
    item_type: Literal["product", "promotion"] = "product"

    product_id: str | None = None
    promotion_id: str | None = None
    quantity: int = Field(gt=0)

    # Solo se utiliza cuando item_type == "promotion".
    promotion_selections: list[PromotionSelectionLoad] = []


class OrderItemCreate(BaseModel):

    item_type: Literal["product", "promotion"] = "product"

    product_id: str | None = None
    promotion_id: str | None = None
    name: str
    quantity: int
    unit_price: float
    subtotal: float

    # Snapshot de las selecciones de la promoción dentro de esta OrderItem.
    promotion_selections: list[PromotionSelectionResponse] = []

    status: bool = True


class OrderItemUpdate(BaseModel):

    item_type: Literal["product", "promotion"] | None = None
    product_id: str | None = None
    promotion_id: str | None = None
    name: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    subtotal: float | None = None
    promotion_selections: list[PromotionSelectionResponse] | None = None
    status: bool | None = None


class OrderItemResponse(OrderItemCreate, MongoModel):
    pass
