from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schema.base_schema import MongoModel


# =========================================================
# TIPOS
# =========================================================

CashRegisterShift = Literal[
    "morning",
    "night"
]

CashRegisterStatus = Literal[
    "open",
    "close"
]


# =========================================================
# CREAR CAJA
# =========================================================

class CashRegisterCreate(BaseModel):

    date: str

    shift: CashRegisterShift

    opened_at: datetime

    opening_amount: float

    status_cash_register: CashRegisterStatus = "open"

    status: bool = True


# =========================================================
# ACTUALIZAR / CERRAR CAJA
# =========================================================

class CashRegisterUpdate(BaseModel):

    date: str | None = None

    shift: CashRegisterShift | None = None

    opened_at: datetime | None = None

    opening_amount: float | None = None

    # -----------------------------------------------------
    # RESUMEN DE VENTAS
    # -----------------------------------------------------

    sales_total: float | None = None

    sales_cash: float | None = None

    sales_transfer: float | None = None

    sales_qr: float | None = None

    sales_debit_card: float | None = None

    # -----------------------------------------------------
    # MOVIMIENTOS MANUALES
    # -----------------------------------------------------

    # Total de ingresos manuales,
    # independientemente del método de pago.
    manual_income: float | None = None

    # Total de egresos manuales,
    # independientemente del método de pago.
    manual_expense: float | None = None

    # -----------------------------------------------------
    # MOVIMIENTOS MANUALES QUE AFECTAN EFECTIVO
    # -----------------------------------------------------

    # Solo ingresos manuales cuyo método de pago es cash.
    manual_income_cash: float | None = None

    # Solo egresos manuales cuyo método de pago es cash.
    manual_expense_cash: float | None = None

    # -----------------------------------------------------
    # EFECTIVO ESPERADO
    # -----------------------------------------------------

    expected_amount: float | None = None

    # -----------------------------------------------------
    # CIERRE
    # -----------------------------------------------------

    closed_at: datetime | None = None

    # Este monto representa SOLO el efectivo físico
    # contado al momento de cerrar la caja.
    closing_amount: float | None = None

    # -----------------------------------------------------
    # DIFERENCIA
    # -----------------------------------------------------

    difference: float | None = None

    # -----------------------------------------------------
    # ESTADO
    # -----------------------------------------------------

    status_cash_register: CashRegisterStatus | None = None

    status: bool | None = None


# =========================================================
# RESPUESTA
# =========================================================

class CashRegisterResponse(
    CashRegisterCreate,
    MongoModel
):

    # -----------------------------------------------------
    # RESUMEN DE VENTAS
    # -----------------------------------------------------

    sales_total: float | None = None

    sales_cash: float | None = None

    sales_transfer: float | None = None

    sales_qr: float | None = None

    sales_debit_card: float | None = None

    # -----------------------------------------------------
    # MOVIMIENTOS MANUALES
    # -----------------------------------------------------

    # Total de ingresos manuales.
    manual_income: float | None = None

    # Total de egresos manuales.
    manual_expense: float | None = None

    # -----------------------------------------------------
    # MOVIMIENTOS MANUALES QUE AFECTAN EFECTIVO
    # -----------------------------------------------------

    manual_income_cash: float | None = None

    manual_expense_cash: float | None = None

    # -----------------------------------------------------
    # CIERRE
    # -----------------------------------------------------

    closed_at: datetime | None = None

    closing_amount: float | None = None

    expected_amount: float | None = None

    difference: float | None = None