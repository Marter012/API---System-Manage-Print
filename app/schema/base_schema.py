from pydantic import BaseModel, ConfigDict,Field


class MongoModel(BaseModel):

    id: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )
