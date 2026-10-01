from fastapi import APIRouter, Depends, Request

from app.services.order_service import OrderService
from app.schema.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
)
from app.websocket.events import broadcast_change
from app.api.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/order",
    tags=["Order"],
)

service = OrderService()


@router.get(
    "/",
    response_model=list[OrderResponse],
)
async def get_orders(current_user = Depends(get_current_user)):
    return await service.get_all()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(order_id: str, current_user = Depends(get_current_user)):
    return await service.get_by_id(order_id)


@router.post(
    "/",
    response_model=OrderResponse,
)
async def create_order(
    data: OrderCreate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.create(data, current_user["sub"])

    # Este único evento representa toda la operación.
    # Crear una orden también puede modificar stock y caja.
    # El frontend, al recibirlo, vuelve a sincronizar esos datos.
    await broadcast_change(
        resource="order",
        action="created",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
)
async def update_order(
    order_id: str,
    data: OrderUpdate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.update(order_id, data, current_user["sub"])

    await broadcast_change(
        resource="order",
        action="updated",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result
