from app.repositories.base_repository import BaseRepository
from app.database.connection import users_collection
from app.utils.exceptions import NotFoundException
from app.utils.serializers import (
    serialize_mongo,
)

class UserRepository(BaseRepository):
    def __init__(self):
        self.collection = users_collection
        
        super().__init__(self.collection)
        
    async def get_by_username(self,username):
        
        document = await self.collection.find_one({"username" : username})
        
        if not document:
            return None
            
        return serialize_mongo(
            document
        )
        
    async def get_by_email(self,email):

        document = await self.collection.find_one({"email" : email})

        if not document:
            return None

        return serialize_mongo(
            document
        )