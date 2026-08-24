from fastapi import FastAPI,HTTPException
from fastapi.exceptions import RequestValidationError
from app.utils.handlers import validation_exception_handler,http_exception_handler,general_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import products,orders,cash_registers,stock_movements,cash_movements

app = FastAPI(
    title= "Boutique de Sabores",
    description = "API gestion",
    version = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(stock_movements.router)
app.include_router(cash_registers.router)
app.include_router(cash_movements.router)

@app.get("/")
def root():
    return{
        "message" : "API Gestion BDS funcionando"
    }