from datetime import datetime

from app.services.base_service import BaseService

from app.repositories.cash_movement_repository import (
    CashMovementRepository
)

from app.repositories.cash_register_repository import (
    CashRegisterRepository
)

from app.repositories.order_repository import (
    OrderRepository
)

from app.utils.object_id import validate_object_id

from app.utils.exceptions import NotFoundException


class CashMovementService(BaseService):

    def __init__(self):

        self.repository = CashMovementRepository()

        self.cash_register_repository = (
            CashRegisterRepository()
        )

        self.order_repository = OrderRepository()

        super().__init__(self.repository)

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    async def create(self, data):

        # -----------------------------------------------------
        # VALIDAR CAJA
        # -----------------------------------------------------

        try:

            object_id_cash = validate_object_id(
                data.cash_register_id
            )

            cash_register = (
                await self.cash_register_repository.get_by_id(
                    object_id_cash
                )
            )

        except NotFoundException:

            raise NotFoundException(
                "No se encontró la caja correspondiente al ID"
            )

        if cash_register["status_cash_register"] != "open":

            raise NotFoundException(
                "No se pueden registrar movimientos "
                "en una caja cerrada"
            )

        # -----------------------------------------------------
        # VALIDAR TIPO
        # -----------------------------------------------------

        if data.type not in [
            "inflow",
            "outflow"
        ]:

            raise NotFoundException(
                "Tipo de movimiento no válido"
            )

        # -----------------------------------------------------
        # VALIDAR MONTO
        # -----------------------------------------------------

        if data.amount <= 0:

            raise NotFoundException(
                "El valor debe ser mayor a 0"
            )

        amount = data.amount

        # -----------------------------------------------------
        # ORDEN RELACIONADA
        # -----------------------------------------------------

        if data.order_id:

            try:

                object_id_order = validate_object_id(
                    data.order_id
                )

                order = (
                    await self.order_repository.get_by_id(
                        object_id_order
                    )
                )

            except NotFoundException:

                raise NotFoundException(
                    "No se encontró la orden correspondiente al ID"
                )

            amount = order["total_price"]

        # -----------------------------------------------------
        # CREAR
        # -----------------------------------------------------

        movement_data = data.model_dump(
            exclude_none=True
        )

        movement_data["amount"] = amount

        if not movement_data.get("date"):

            movement_data["date"] = datetime.now()

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
                "Movimiento de caja no encontrado"
            )

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        if "amount" in update_data:

            if update_data["amount"] <= 0:

                raise NotFoundException(
                    "El valor debe ser mayor a 0"
                )

        if "type" in update_data:

            if update_data["type"] not in [
                "inflow",
                "outflow"
            ]:

                raise NotFoundException(
                    "Tipo de movimiento no válido"
                )

        # Si cambia la orden, tomar su total
        if "order_id" in update_data:

            if update_data["order_id"]:

                try:

                    object_id_order = validate_object_id(
                        update_data["order_id"]
                    )

                    order = (
                        await self.order_repository.get_by_id(
                            object_id_order
                        )
                    )

                except NotFoundException:

                    raise NotFoundException(
                        "No se encontró la orden correspondiente al ID"
                    )

                update_data["amount"] = (
                    order["total_price"]
                )

        # Si se modifica cash_register_id,
        # verificar que la nueva caja esté abierta.
        if "cash_register_id" in update_data:

            try:

                object_id_cash = validate_object_id(
                    update_data["cash_register_id"]
                )

                cash_register = (
                    await self.cash_register_repository
                    .get_by_id(object_id_cash)
                )

            except NotFoundException:

                raise NotFoundException(
                    "No se encontró la caja correspondiente al ID"
                )

            if (
                cash_register["status_cash_register"]
                != "open"
            ):

                raise NotFoundException(
                    "La caja seleccionada está cerrada"
                )

        return await self.repository.update(
            movement_id,
            update_data
        )