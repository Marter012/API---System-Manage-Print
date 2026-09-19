from fastapi import APIRouter

from app.schema.promotion_schema import (
    PromotionCreate,
    PromotionResponse,
    PromotionUpdate,
)
from app.services.promotion_service import PromotionService


router = APIRouter(
    prefix="/promotion",
    tags=["Promotion"]
)

service = PromotionService()


@router.get(
    "/",
    response_model=list[PromotionResponse]
)
async def get_promotions():

    return await service.get_all()


@router.get(
    "/{promotion_id}",
    response_model=PromotionResponse
)
async def get_promotion(
    promotion_id: str
):

    return await service.get_by_id(promotion_id)


@router.post(
    "/",
    response_model=PromotionResponse
)
async def create_promotion(
    data: PromotionCreate
):

    return await service.create(data)


@router.put(
    "/{promotion_id}",
    response_model=PromotionResponse
)
async def update_promotion(
    promotion_id: str,
    data: PromotionUpdate
):

    return await service.update(
        promotion_id,
        data
    )
