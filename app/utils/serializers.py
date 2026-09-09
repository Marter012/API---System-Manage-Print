from datetime import datetime
from app.utils.dateZone import DateUtils


def serialize_mongo(document: dict) -> dict:

    if not document:
        return None

    document["id"] = str(document.pop("_id"))

    for key, value in document.items():

        if isinstance(value, datetime):

            document[key] = DateUtils.to_argentina(value)

    return document


def serialize_mongo_list(documents: list) -> list:

    return [
        serialize_mongo(document)
        for document in documents
    ]