from bson import ObjectId
from app.utils.exceptions import BadRequestException  

def validate_object_id(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise BadRequestException("Invalid ID format")
    
    return ObjectId(id)