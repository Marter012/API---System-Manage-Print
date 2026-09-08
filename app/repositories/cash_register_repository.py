from app.repositories.base_repository import BaseRepository

from app.database.connection import (
    cash_register_collection
)

from app.utils.serializers import (
    serialize_mongo
)


class CashRegisterRepository(
    BaseRepository
):

    def __init__(self):

        self.collection = cash_register_collection

        super().__init__(
            self.collection
        )

    async def get_by_date_and_shift(
        self,
        date: str,
        shift: str
    ):

        document = await self.collection.find_one(
            {
                "date": date,
                "shift": shift,
                "status": True
            }
        )

        if not document:

            return None

        return serialize_mongo(
            document
        )

    async def get_by_date(
        self,
        date: str
    ):

        documents = []

        cursor = self.collection.find(
            {
                "date": date,
                "status": True
            }
        )

        async for document in cursor:

            documents.append(
                serialize_mongo(
                    document
                )
            )

        return documents

    async def get_open_register(
        self
    ):

        document = await self.collection.find_one(
            {
                "status_cash_register": "open",
                "status": True
            }
        )

        if not document:

            return None

        return serialize_mongo(
            document
        )