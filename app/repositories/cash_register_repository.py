from app.repositories.base_repository import BaseRepository
from app.database.connection import cash_register_collection
from app.utils.serializers import serialize_mongo


class CashRegisterRepository(BaseRepository):

    def __init__(self):
        self.collection = cash_register_collection
        super().__init__(self.collection)

    async def get_open_register(self):

        document = await self.collection.find_one(
            {
                "status_cash_register": "open",
                "status": True
            }
        )

        if not document:
            return None

        return serialize_mongo(document)