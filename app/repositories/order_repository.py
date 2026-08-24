from app.repositories.base_repository import BaseRepository
from app.database.connection import orders_collection

class OrderRepository(BaseRepository):
    def __init__(self):
        self.collection = orders_collection
        super().__init__(orders_collection)
        
    