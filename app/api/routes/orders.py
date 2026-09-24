from fastapi import APIRouter, Request

from app.services.order_service import OrderService
from app.schema.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
)
from app.websocket.events import broadcast_change


router = APIRouter(
    prefix="/order",
    tags=["Order"],
)

service = OrderService()


@router.get(
    "/",
    response_model=list[OrderResponse],
)
async def get_orders():
    return await service.get_all()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(order_id: str):
    return await service.get_by_id(order_id)


@router.post(
    "/",
    response_model=OrderResponse,
)
async def create_order(
    data: OrderCreate,
    request: Request,
):
    result = await service.create(data)

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
):
    result = await service.update(order_id, data)

    await broadcast_change(
        resource="order",
        action="updated",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result
