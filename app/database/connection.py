from motor.motor_asyncio import AsyncIOMotorClient

from app.config.settings import settings


client = AsyncIOMotorClient(
    settings.MONGO_URL
)

database = client[settings.MONGO_DB_NAME]


products_collection = database["products"]
promotions_collection = database["promotions"]
orders_collection = database["orders"]
order_item_collection = database["order_items"]
stock_movement_collection = database["stock_movements"]
cash_movement_collection = database["cash_movements"]
cash_register_collection = database["cash_registers"]
users_collection = database["users"]
password_reset_collection = database["password_reset"]