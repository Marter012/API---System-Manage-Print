from app.services.base_service import BaseService

from app.repositories.stock_movement_repository import (
    StockMovementRepository
)

from app.repositories.product_repository import (
    ProductRepository
)

from app.utils.exceptions import NotFoundException


class StockMovementService(BaseService):

    def __init__(self):

        self.repository = StockMovementRepository()

        self.product_repository = ProductRepository()

        super().__init__(self.repository)

    # ---------------------------------------------------------
    # EFFECT
    # ---------------------------------------------------------

    def _effect(
        self,
        movement_type: str,
        quantity: int
    ):

        if movement_type == "inflow":

            return quantity

        if movement_type == "outflow":

            return -quantity

        raise NotFoundException(
            "Tipo de movimiento no válido"
        )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    async def create(self, data):

        if data.quantity <= 0:

            raise NotFoundException(
                "La cantidad debe ser mayor a 0"
            )

        if data.type not in [
            "inflow",
            "outflow"
        ]:

            raise NotFoundException(
                "Tipo de movimiento no válido"
            )

        product = await self.product_repository.get_by_id(
            data.product_id
        )

        if not product:

            raise NotFoundException(
                "Producto no encontrado"
            )

        effect = self._effect(
            data.type,
            data.quantity
        )

        new_quantity = (
            product["quantity"] + effect
        )

        if new_quantity < 0:

            raise NotFoundException(
                f"No hay stock suficiente del producto "
                f"'{product['name']}'. "
                f"Disponible: {product['quantity']}"
            )

        # Actualizar stock
        await self.product_repository.update(
            data.product_id,
            {
                "quantity": new_quantity
            }
        )

        movement_data = data.model_dump(
            exclude_none=True
        )

        return await self.repository.create(
            movement_data
        )

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    async def update(
        self,
        movement_id,
        data
    ):

        old = await self.repository.get_by_id(
            movement_id
        )

        if not old:

            raise NotFoundException(
                "Movimiento no encontrado"
            )

        old_product_id = old["product_id"]

        old_type = old["type"]

        old_quantity = old["quantity"]

        old_effect = self._effect(
            old_type,
            old_quantity
        )

        new_product_id = (
            data.product_id
            if data.product_id is not None
            else old_product_id
        )

        new_type = (
            data.type
            if data.type is not None
            else old_type
        )

        new_quantity = (
            data.quantity
            if data.quantity is not None
            else old_quantity
        )

        if new_quantity <= 0:

            raise NotFoundException(
                "La cantidad debe ser mayor a 0"
            )

        if new_type not in [
            "inflow",
            "outflow"
        ]:

            raise NotFoundException(
                "Tipo de movimiento no válido"
            )

        old_product = await self.product_repository.get_by_id(
            old_product_id
        )

        if not old_product:

            raise NotFoundException(
                "Producto anterior no encontrado"
            )

        # Revertir movimiento anterior
        old_product_quantity = (
            old_product["quantity"]
            - old_effect
        )

        if old_product_quantity < 0:

            raise NotFoundException(
                "No se puede revertir el movimiento"
            )

        # -----------------------------------------------------
        # MISMO PRODUCTO
        # -----------------------------------------------------

        if old_product_id == new_product_id:

            new_effect = self._effect(
                new_type,
                new_quantity
            )

            final_quantity = (
                old_product_quantity
                + new_effect
            )

            if final_quantity < 0:

                raise NotFoundException(
                    f"No hay stock suficiente del producto "
                    f"'{old_product['name']}'"
                )

            await self.product_repository.update(
                old_product_id,
                {
                    "quantity": final_quantity
                }
            )

        # -----------------------------------------------------
        # PRODUCTO DIFERENTE
        # -----------------------------------------------------

        else:

            new_product = await self.product_repository.get_by_id(
                new_product_id
            )

            if not new_product:

                raise NotFoundException(
                    "Nuevo producto no encontrado"
                )

            # Restaurar producto anterior
            await self.product_repository.update(
                old_product_id,
                {
                    "quantity": old_product_quantity
                }
            )

            new_effect = self._effect(
                new_type,
                new_quantity
            )

            final_quantity = (
                new_product["quantity"]
                + new_effect
            )

            if final_quantity < 0:

                # Restaurar producto anterior
                await self.product_repository.update(
                    old_product_id,
                    {
                        "quantity": old_product["quantity"]
                    }
                )

                raise NotFoundException(
                    f"No hay stock suficiente del producto "
                    f"'{new_product['name']}'"
                )

            await self.product_repository.update(
                new_product_id,
                {
                    "quantity": final_quantity
                }
            )

        # Actualizar documento del movimiento
        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        return await self.repository.update(
            movement_id,
            update_data
        )