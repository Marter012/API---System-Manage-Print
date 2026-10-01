from contextlib import asynccontextmanager

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
    users,
    auth
)
from app.utils.handlers import (
    validation_exception_handler,
)
from app.websocket.router import router as websocket_router
from app.database.indexes import create_indexes
from app.database.seed import create_initial_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    await create_initial_admin()

    yield


app = FastAPI(
    title="Boutique de Sabores",
    description="API gestion",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(websocket_router)


@app.get("/")
def root():
    return {
        "message": "API Gestion BDS funcionando"
    }