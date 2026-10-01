from fastapi import APIRouter,Depends
from app.services.user_service import UserService
from app.schema.user_schema import UserCreate,UserResponse,UserUpdate
from app.api.dependencies.auth import require_admin

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

service = UserService()

@router.get(
    "/",
    response_model=list[UserResponse],
)
async def get_users(current_user = Depends(require_admin)):
    
    return await service.get_all()

@router.get(
    "/{user_id}",
    response_model=UserResponse
)
async def get_user(user_id : str,current_user = Depends(require_admin)):

    return await service.get_by_id(user_id)

@router.post(
    "/",
    response_model=UserResponse
)
async def create_user(user : UserCreate,current_user=Depends(require_admin)):
    
    return await service.create(user)

@router.put(
    "/{user_id}",
    response_model=UserResponse
)
async def update_user(user_id : str, user:UserUpdate,current_user=Depends(require_admin)):
        
    return await service.update(user_id,user)
