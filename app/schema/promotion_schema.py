from pydantic import BaseModel, Field
from app.schema.base_schema import MongoModel


class PromotionItemCreate(BaseModel):
    """Grupo de composición de una promoción.

    Ejemplo: 6 unidades del grupo 'Empanadas clásicas',
    permitiendo elegir entre determinados product_id.
    """

    name: str
    quantity: int = Field(gt=0)
    product_ids: list[str] = Field(min_length=1)


class PromotionItemResponse(PromotionItemCreate, MongoModel):
    pass


class PromotionCreate(BaseModel):

    name: str
    description: str = ""
    price: float = Field(ge=0)
    items: list[PromotionItemCreate] = Field(min_length=1)
    status: bool = True


class PromotionUpdate(BaseModel):

    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    items: list[PromotionItemCreate] | None = None
    status: bool | None = None


class PromotionResponse(PromotionCreate, MongoModel):

    items: list[PromotionItemResponse]
