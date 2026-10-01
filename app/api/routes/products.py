from fastapi import APIRouter, Depends, Request

from app.schema.product_schema import (
    ProductResponse,
    ProductCreate,
    ProductUpdate,
)
from app.services.product_service import ProductService
from app.websocket.events import broadcast_change
from app.api.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/product",
    tags=["Product"],
)

service = ProductService()


@router.get(
    "/",
    response_model=list[ProductResponse],
)
async def get_products(current_user = Depends(get_current_user)):
    return await service.get_all()


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(product_id: str, current_user = Depends(get_current_user)):
    return await service.get_by_id(product_id)


@router.post(
    "/",
    response_model=ProductResponse,
)
async def create_product(
    product: ProductCreate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.create(product)

    await broadcast_change(
        resource="product",
        action="created",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    request: Request,
    current_user = Depends(get_current_user),
):
    result = await service.update(product_id, product)

    await broadcast_change(
        resource="product",
        action="updated",
        data=result,
        source_client_id=request.headers.get("X-Client-ID"),
    )

    return result
