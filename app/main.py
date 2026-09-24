from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    products,
    orders,
    cash_registers,
    stock_movements,
    cash_movements,
    promotions,
)
from app.utils.handlers import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.websocket.router import router as websocket_router


app = FastAPI(
    title="Boutique de Sabores",
    description="API gestion",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://system-manage-print.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(stock_movements.router)
app.include_router(cash_registers.router)
app.include_router(cash_movements.router)
app.include_router(promotions.router)
app.include_router(websocket_router)


@app.get("/")
def root():
    return {
        "message": "API Gestion BDS funcionando"
    }
