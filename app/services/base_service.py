from app.repositories.base_repository import BaseRepository


class BaseService:

    def __init__(
        self,
        repository: BaseRepository
    ):

        self.repository = repository

    async def get_all(self):

        return await self.repository.get_all()

    async def get_by_id(
        self,
        document_id
    ):

        return await self.repository.get_by_id(
            document_id
        )

    async def create(
        self,
        data
    ):

        return await self.repository.create(
            data.model_dump(
                exclude_none=True
            )
        )

    async def update(
        self,
        document_id,
        data
    ):

        return await self.repository.update(
            document_id,
            data.model_dump(
                exclude_none=True,
                exclude_unset=True
            )
        )