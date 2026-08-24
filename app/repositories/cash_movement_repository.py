from app.repositories.base_repository import BaseRepository
from app.database.connection import cash_movement_collection
from app.utils.serializers import serialize_mongo


class CashMovementRepository(BaseRepository):

    def __init__(self):
        self.collection = cash_movement_collection
        super().__init__(self.collection)

    async def get_by_cash_register_id(
        self,
        cash_register_id: str
    ):

        documents = []

        cursor = self.collection.find({
            "cash_register_id": str(cash_register_id),
            "status": True
        })

        async for document in cursor:

            documents.append(
                serialize_mongo(document)
            )

        return documents