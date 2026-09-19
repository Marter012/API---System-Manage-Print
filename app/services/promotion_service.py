from uuid import uuid4

from app.services.base_service import BaseService
from app.repositories.promotion_repository import PromotionRepository
from app.repositories.product_repository import ProductRepository
from app.utils.exceptions import NotFoundException


class PromotionService(BaseService):

    def __init__(self):

        self.repository = PromotionRepository()
        self.product_repository = ProductRepository()

        super().__init__(self.repository)

    async def _prepare_items(self, items):

        if not items:
            raise NotFoundException(
                "Una promoción debe tener al menos un grupo de composición"
            )

        prepared = []

        for item in items:

            if item.quantity <= 0:
                raise NotFoundException(
                    "La cantidad de un grupo de promoción debe ser mayor a 0"
                )

            if not item.product_ids:
                raise NotFoundException(
                    "Cada grupo de promoción debe tener al menos un producto permitido"
                )

            product_ids = []

            for product_id in item.product_ids:

                product = await self.product_repository.get_by_id(product_id)

                if not product:
                    raise NotFoundException(
                        f"El producto con ID {product_id} no existe"
                    )

                if not product["status"]:
                    raise NotFoundException(
                        f"El producto '{product['name']}' está inactivo y no puede formar parte de una promoción"
                    )

                product_id = str(product_id)

                if product_id not in product_ids:
                    product_ids.append(product_id)

            prepared.append({
                "id": str(uuid4()),
                "name": item.name,
                "quantity": item.quantity,
                "product_ids": product_ids,
            })

        return prepared

    async def create(self, data):

        items = await self._prepare_items(data.items)

        promotion_data = {
            "name": data.name,
            "description": data.description,
            "price": data.price,
            "items": items,
            "status": data.status,
        }

        return await self.repository.create(promotion_data)

    async def update(self, promotion_id, data):

        current = await self.repository.get_by_id(promotion_id)

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        if data.items is not None:
            update_data["items"] = await self._prepare_items(data.items)

        # Si solo se modifican datos generales, conservamos los grupos actuales.
        if not update_data:
            return current

        return await self.repository.update(
            promotion_id,
            update_data
        )
