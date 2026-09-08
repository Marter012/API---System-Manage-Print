from app.repositories.base_repository import BaseRepository

from app.database.connection import (
    stock_movement_collection
)


class StockMovementRepository(
    BaseRepository
):

    def __init__(self):

        self.collection = stock_movement_collection

        super().__init__(
            self.collection
        )