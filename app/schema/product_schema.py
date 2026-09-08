from pydantic import BaseModel

from app.schema.base_schema import MongoModel


class ProductCreate(BaseModel):

    name: str

    category: str

    price: float

    quantity: int

    status: bool = True


class ProductUpdate(BaseModel):

    name: str | None = None

    category: str | None = None

    price: float | None = None

    quantity: int | None = None

    status: bool | None = None


class ProductResponse(
    ProductCreate,
    MongoModel
):

    pass