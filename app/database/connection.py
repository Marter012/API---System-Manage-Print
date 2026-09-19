from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

client = AsyncIOMotorClient(settings.MONGO_URL)

database = client[settings.DATABASE_NAME]

products_collection = database["products"]
promotions_collection = database["promotions"]
orders_collection = database["orders"]
order_item_collection = database["order_item"]
stock_movement_collection = database["stock_movement"]
cash_movement_collection = database["cash_movement"]
cash_register_collection = database["cash_register"]
