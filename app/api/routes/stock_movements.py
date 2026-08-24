from fastapi import APIRouter
from app.services.stock_movement_service import StockMovementService
from app.schema.stock_movement_schema import StockMovementResponse,StockMovementCreate,StockMovementUpdate

router= APIRouter(
    prefix="/stockMovement",
    tags=["StockMovement"]
)

service = StockMovementService()


@router.get(
    "/",
    response_model=list[StockMovementResponse]
)
async def get_stock_movements():
    return await service.get_all()


@router.get(
    "/{stock_movement_id}",
    response_model=StockMovementResponse
)
async def get_stock_movement(stock_movement_id : str ):
    return await service.get_by_id(stock_movement_id)

@router.post(
    "/",
    response_model=StockMovementResponse
)
async def create_stock_movement(data : StockMovementCreate):
    return await service.create(data )

@router.put(
    "/",
    response_model=StockMovementResponse
)
async def update_stock_movement(stock_movement_id : str ,data : StockMovementUpdate):
    return await service.update(stock_movement_id,data)