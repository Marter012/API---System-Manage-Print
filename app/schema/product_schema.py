from pydantic import BaseModel

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

class ProductResponse(BaseModel):

    id: str
    name: str
    category: str
    price: float
    quantity: int
    status: bool