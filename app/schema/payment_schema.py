from typing import Literal


PaymentMethod = Literal[
    "cash",
    "transfer",
    "qr",
    "debit_card",
    "mercado_pago"
]


PaymentStatus = Literal[
    "pending",
    "paid",
    "cancelled"
]


CashMovementType = Literal[
    "inflow",
    "outflow"
]