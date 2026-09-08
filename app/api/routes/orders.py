from fastapi import APIRouter

from app.services.order_service import (
    OrderService
)

from app.schema.order_schema import (
    OrderCreate,
    OrderResponse,
    OrderUpdate
)


router = APIRouter(

    prefix="/order",

    tags=["Order"]

)


service = OrderService()


# =========================================================
# GET ALL ORDERS
# =========================================================

@router.get(
    "/",
    response_model=list[OrderResponse]
)
async def get_orders():

    return await service.get_all()


# =========================================================
# GET ORDER BY ID
# =========================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
async def get_order(
    order_id: str
):

    return await service.get_by_id(
        order_id
    )


# =========================================================
# CREATE ORDER
# =========================================================

@router.post(
    "/",
    response_model=OrderResponse
)
async def create_order(
    data: OrderCreate
):

    return await service.create(
        data
    )


# =========================================================
# UPDATE ORDER
# =========================================================

@router.put(
    "/{order_id}",
    response_model=OrderResponse
)
async def update_order(
    order_id: str,
    data: OrderUpdate
):

    return await service.update(
        order_id,
        data
    )