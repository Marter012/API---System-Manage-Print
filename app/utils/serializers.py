def serialize_mongo(document: dict) -> dict:

    if not document:
        return None

    document["id"] = str(document.pop("_id"))

    return document

def serialize_mongo_list(documents: list) -> list:
    
    return [serialize_mongo(document) for document in documents]