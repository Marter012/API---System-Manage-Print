from fastapi import APIRouter, Depends, Request

from app.services.stock_movement_service import StockMovementService
from app.schema.stock_movement_schema import (
    StockMovementResponse,
    StockMovementCreate,
    StockMovementUpdate,
)
from app.websocket.events import broadcast_change
from app.api.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/stockMovement",
    tags=["StockMovement"],
)

service = StockMovementService()


@router.get(
    "/",
    response_model=list[StockMovementResponse],
)
async def get_stock_movements(current_user = Depends(get_current_user)):
    return await service.get_all()


@router.get(
    "/{stock_movement_id}",
    response_model=StockMovementResponse,
)
async def get_stock_movement(stock_movement_id: str, current_user = Depends(get_current_user)):
    return await service.get_by_id(stock_movement_id)


@router.post(
    "/",
    response_model=StockMovementResponse,
)
async def create_stock_movement(
    data: StockMovementCreate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.create(data)

    await broadcast_change(
        resource="stock_movement",
        action="created",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result


@router.put(
    "/{stock_movement_id}",
    response_model=StockMovementResponse,
)
async def update_stock_movement(
    stock_movement_id: str,
    data: StockMovementUpdate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.update(stock_movement_id, data)

    await broadcast_change(
        resource="stock_movement",
        action="updated",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result
