from fastapi import APIRouter
from app.schema.product_schema import ProductResponse,ProductCreate,ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(
    prefix="/product",
    tags=["Product"]
)

service = ProductService()

@router.get(
    "/",
    response_model= list[ProductResponse]
)
async def get_products():
    return await service.get_all()

@router.get(
    "/{product_id}",
    response_model= ProductResponse
)
async def get_product(product_id : str):
    return await service.get_by_id(product_id)

@router.post(
    "/",
    response_model= ProductResponse
)
async def create_product(product: ProductCreate):
    
    return await service.create(product)

@router.put(
    "/{product_id}",
    response_model= ProductResponse
)
async def update_product(product_id : str,product : ProductUpdate):
    
    return await service.update(product_id,product)