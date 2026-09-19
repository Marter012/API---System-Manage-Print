from app.repositories.base_repository import BaseRepository
from app.database.connection import promotions_collection


class PromotionRepository(BaseRepository):

    def __init__(self):

        self.collection = promotions_collection

        super().__init__(self.collection)
