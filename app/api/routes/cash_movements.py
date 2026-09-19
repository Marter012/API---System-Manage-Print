from fastapi import APIRouter

from app.services.cash_movement_service import CashMovementService

from app.schema.cash_movement_schema import (
    CashMovementCreate,
    CashMovementResponse,
    CashMovementUpdate
)


router = APIRouter(
    prefix="/cashMovement",
    tags=["CashMovement"]
)


service = CashMovementService()


@router.get(
    "/",
    response_model=list[CashMovementResponse]
)
async def get_cash_movements():

    return await service.get_all()


@router.get(
    "/{cash_movement_id}",
    response_model=CashMovementResponse
)
async def get_cash_movement(
    cash_movement_id: str
):

    return await service.get_by_id(
        cash_movement_id
    )


@router.post(
    "/",
    response_model=CashMovementResponse
)
async def create_cash_movement(
    data: CashMovementCreate
):

    return await service.create(
        data
    )


@router.put(
    "/{cash_movement_id}",
    response_model=CashMovementResponse
)
async def update_cash_movement(
    cash_movement_id: str,
    data: CashMovementUpdate
):

    return await service.update(
        cash_movement_id,
        data
    )
