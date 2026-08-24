from pydantic import BaseModel

from app.schema.base_schema import MongoModel


class StockMovementCreate(BaseModel):

    product_id: str

    # inflow = ingreso
    # outflow = egreso
    type: str

    description: str

    quantity: int

    # Orden que originó el movimiento
    order_id: str | None = None

    status: bool = True


class StockMovementUpdate(BaseModel):

    product_id: str | None = None

    type: str | None = None

    description: str | None = None

    quantity: int | None = None

    order_id: str | None = None

    status: bool | None = None


class StockMovementResponse(
    StockMovementCreate,
    MongoModel
):
    pass