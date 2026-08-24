from app.repositories.base_repository import BaseRepository
from app.database.connection import stock_movement_collection

class StockMovementRepository(BaseRepository):
    def __init__(self):
        super().__init__(stock_movement_collection)