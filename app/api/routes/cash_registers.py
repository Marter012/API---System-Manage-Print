from fastapi import APIRouter

from app.services.cash_register_service import (
    CashRegisterService
)

from app.schema.cash_registers_schema import (
    CashRegisterResponse,
    CashRegisterCreate,
    CashRegisterUpdate
)


router = APIRouter(

    prefix="/cashRegister",

    tags=["CashRegister"]

)


service = CashRegisterService()


# =========================================================
# GET ALL CASH REGISTERS
# =========================================================

@router.get(
    "/",
    response_model=list[CashRegisterResponse]
)
async def get_cash_registers():

    return await service.get_all()


# =========================================================
# GET CASH REGISTER BY ID
# =========================================================

@router.get(
    "/{cash_register_id}",
    response_model=CashRegisterResponse
)
async def get_cash_register(
    cash_register_id: str
):

    return await service.get_by_id(
        cash_register_id
    )


# =========================================================
# CREATE CASH REGISTER
# =========================================================

@router.post(
    "/",
    response_model=CashRegisterResponse
)
async def create_cash_register(
    data: CashRegisterCreate
):

    return await service.create(
        data
    )


# =========================================================
# UPDATE CASH REGISTER
# =========================================================

@router.put(
    "/{cash_register_id}",
    response_model=CashRegisterResponse
)
async def update_cash_register(
    cash_register_id: str,
    data: CashRegisterUpdate
):

    return await service.update(
        cash_register_id,
        data
    )