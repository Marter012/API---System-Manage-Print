from app.repositories.base_repository import BaseRepository
from app.database.connection import password_reset_collection
from app.utils.serializers import serialize_mongo
from app.utils.object_id import validate_object_id


class PasswordResetRepository(BaseRepository):

    def __init__(self):
        self.collection = password_reset_collection
        super().__init__(self.collection)

    async def get_by_user_id(self, user_id):

        document = await self.collection.find_one(
            {
                "user_id": user_id,
                "used": False
            }
        )

        if not document:
            return None

        return serialize_mongo(document)

    async def invalidate_by_user_id(self, user_id):

        await self.collection.update_many(
            {
                "user_id": user_id,
                "used": False
            },
            {
                "$set": {
                    "used": True
                }
            }
        )

    async def mark_as_used(self, document_id):

        object_id = validate_object_id(
            document_id
        )

        await self.collection.update_one(
            {
                "_id": object_id
            },
            {
                "$set": {
                    "used": True
                }
            }
        )