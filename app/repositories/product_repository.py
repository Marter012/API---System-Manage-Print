from app.repositories.base_repository import BaseRepository

from app.database.connection import (
    products_collection
)


class ProductRepository(
    BaseRepository
):

    def __init__(self):

        self.collection = products_collection

        super().__init__(
            self.collection
        )