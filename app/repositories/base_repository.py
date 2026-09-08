from app.utils.serializers import (
    serialize_mongo,
)
from app.utils.object_id import validate_object_id
from app.utils.exceptions import NotFoundException


class BaseRepository:

    def __init__(self, collection):

        self.collection = collection

    async def get_all(self):

        documents = []

        async for document in self.collection.find():

            documents.append(
                serialize_mongo(document)
            )

        return documents

    async def get_by_id(
        self,
        document_id
    ):

        object_id = validate_object_id(
            document_id
        )

        document = await self.collection.find_one(
            {
                "_id": object_id
            }
        )

        if not document:

            raise NotFoundException(
                "Resource not found"
            )

        return serialize_mongo(
            document
        )

    async def create(
        self,
        data
    ):

        result = await self.collection.insert_one(
            data
        )

        return await self.get_by_id(
            str(result.inserted_id)
        )

    async def update(
        self,
        document_id,
        data
    ):

        object_id = validate_object_id(
            document_id
        )

        result = await self.collection.update_one(
            {
                "_id": object_id
            },
            {
                "$set": data
            }
        )

        if result.matched_count == 0:

            raise NotFoundException(
                "Resource not found"
            )

        return await self.get_by_id(
            document_id
        )