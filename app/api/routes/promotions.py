from fastapi import APIRouter, Request

from app.schema.promotion_schema import (
    PromotionCreate,
    PromotionResponse,
    PromotionUpdate,
)
from app.services.promotion_service import PromotionService
from app.websocket.events import broadcast_change


router = APIRouter(
    prefix="/promotion",
    tags=["Promotion"],
)

service = PromotionService()


@router.get(
    "/",
    response_model=list[PromotionResponse],
)
async def get_promotions():
    return await service.get_all()


@router.get(
    "/{promotion_id}",
    response_model=PromotionResponse,
)
async def get_promotion(promotion_id: str):
    return await service.get_by_id(promotion_id)


@router.post(
    "/",
    response_model=PromotionResponse,
)
async def create_promotion(
    data: PromotionCreate,
    request: Request,
):
    result = await service.create(data)

    await broadcast_change(
        resource="promotion",
        action="created",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result


@router.put(
    "/{promotion_id}",
    response_model=PromotionResponse,
)
async def update_promotion(
    promotion_id: str,
    data: PromotionUpdate,
    request: Request,
):
    result = await service.update(promotion_id, data)

    await broadcast_change(
        resource="promotion",
        action="updated",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result
