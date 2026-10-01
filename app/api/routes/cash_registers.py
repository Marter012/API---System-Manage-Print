from fastapi import APIRouter, Depends, Request

from app.services.cash_register_service import CashRegisterService
from app.schema.cash_registers_schema import (
    CashRegisterResponse,
    CashRegisterCreate,
    CashRegisterUpdate,
)
from app.websocket.events import broadcast_change
from app.api.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/cashRegister",
    tags=["CashRegister"],
)

service = CashRegisterService()


@router.get(
    "/",
    response_model=list[CashRegisterResponse],
)
async def get_cash_registers(current_user = Depends(get_current_user)):
    return await service.get_all()


@router.get(
    "/{cash_register_id}",
    response_model=CashRegisterResponse,
)
async def get_cash_register(cash_register_id: str, current_user = Depends(get_current_user)):
    return await service.get_by_id(cash_register_id)


@router.post(
    "/",
    response_model=CashRegisterResponse,
)
async def create_cash_register(
    data: CashRegisterCreate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.create(data, current_user["sub"])

    await broadcast_change(
        resource="cash_register",
        action="created",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result


@router.put(
    "/{cash_register_id}",
    response_model=CashRegisterResponse,
)
async def update_cash_register(
    cash_register_id: str,
    data: CashRegisterUpdate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.update(cash_register_id, data, current_user["sub"])

    await broadcast_change(
        resource="cash_register",
        action="updated",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result
