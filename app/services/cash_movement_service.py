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


class CashMovementService(
    BaseService
):

    def __init__(self):

        self.repository = CashMovementRepository()

        self.cash_register_repository = (
            CashRegisterRepository()
        )

        self.order_repository = OrderRepository()

        super().__init__(
            self.repository
        )

    # =========================================================
    # CREATE
    # =========================================================

    async def create(
        self,
        data
    ):

        # -----------------------------------------------------
        # VALIDAR CAJA
        # -----------------------------------------------------

        try:

            validate_object_id(
                data.cash_register_id
            )

            cash_register = (
                await self.cash_register_repository.get_by_id(
                    data.cash_register_id
                )
            )

        except NotFoundException:

            raise NotFoundException(
                "No se encontró la caja correspondiente al ID"
            )

        if not cash_register:

            raise NotFoundException(
                "No se encontró la caja correspondiente al ID"
            )

        # -----------------------------------------------------
        # VERIFICAR ESTADO DE CAJA
        # -----------------------------------------------------

        if (
            cash_register["status_cash_register"]
            != "open"
        ):

            raise NotFoundException(
                "No se pueden registrar movimientos "
                "en una caja cerrada"
            )

        # -----------------------------------------------------
        # VALIDAR MONTO
        # -----------------------------------------------------

        if data.amount <= 0:

            raise NotFoundException(
                "El valor debe ser mayor a 0"
            )

        amount = data.amount

        # =====================================================
        # SI EL MOVIMIENTO PERTENECE A UNA ORDEN
        # =====================================================

        if data.order_id:

            try:

                validate_object_id(
                    data.order_id
                )

                order = (
                    await self.order_repository.get_by_id(
                        data.order_id
                    )
                )

            except NotFoundException:

                raise NotFoundException(
                    "No se encontró la orden correspondiente al ID"
                )

            if not order:

                raise NotFoundException(
                    "No se encontró la orden correspondiente al ID"
                )

            # -------------------------------------------------
            # VERIFICAR QUE LA ORDEN PERTENEZCA A LA CAJA
            # -------------------------------------------------

            order_cash_register_id = (
                order.get("cash_register_id")
            )

            if (
                order_cash_register_id
                and
                str(order_cash_register_id)
                != str(data.cash_register_id)
            ):

                raise NotFoundException(
                    "La orden no pertenece a la caja seleccionada"
                )

            # -------------------------------------------------
            # EL MONTO DE UNA ORDEN SIEMPRE ES SU TOTAL
            # -------------------------------------------------

            amount = order["total_price"]

        # -----------------------------------------------------
        # PREPARAR MOVIMIENTO
        # -----------------------------------------------------

        movement_data = data.model_dump(
            exclude_none=True
        )

        movement_data["amount"] = amount

        if not movement_data.get("date"):

            movement_data["date"] = datetime.now()

        # -----------------------------------------------------
        # CREAR MOVIMIENTO
        # -----------------------------------------------------

        return await self.repository.create(
            movement_data
        )

    # =========================================================
    # UPDATE
    # =========================================================

    async def update(
        self,
        movement_id,
        data
    ):

        # -----------------------------------------------------
        # OBTENER MOVIMIENTO ANTERIOR
        # -----------------------------------------------------

        old = await self.repository.get_by_id(
            movement_id
        )

        if not old:

            raise NotFoundException(
                "Movimiento de caja no encontrado"
            )

        # -----------------------------------------------------
        # DATOS A ACTUALIZAR
        # -----------------------------------------------------

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # -----------------------------------------------------
        # VALIDAR MONTO
        # -----------------------------------------------------

        if "amount" in update_data:

            if update_data["amount"] <= 0:

                raise NotFoundException(
                    "El valor debe ser mayor a 0"
                )

        # =====================================================
        # VALIDAR ORDEN
        # =====================================================

        if "order_id" in update_data:

            if update_data["order_id"]:

                try:

                    validate_object_id(
                        update_data["order_id"]
                    )

                    order = (
                        await self.order_repository.get_by_id(
                            update_data["order_id"]
                        )
                    )

                except NotFoundException:

                    raise NotFoundException(
                        "No se encontró la orden correspondiente al ID"
                    )

                if not order:

                    raise NotFoundException(
                        "No se encontró la orden correspondiente al ID"
                    )

                # ---------------------------------------------
                # DETERMINAR CAJA
                # ---------------------------------------------

                selected_cash_register_id = (
                    update_data.get(
                        "cash_register_id",
                        old.get("cash_register_id")
                    )
                )

                order_cash_register_id = (
                    order.get("cash_register_id")
                )

                if (
                    order_cash_register_id
                    and
                    str(order_cash_register_id)
                    != str(selected_cash_register_id)
                ):

                    raise NotFoundException(
                        "La orden no pertenece "
                        "a la caja seleccionada"
                    )

                update_data["amount"] = (
                    order["total_price"]
                )

        # =====================================================
        # VALIDAR CAJA
        # =====================================================

        if "cash_register_id" in update_data:

            try:

                validate_object_id(
                    update_data["cash_register_id"]
                )

                cash_register = (
                    await self.cash_register_repository
                    .get_by_id(
                        update_data["cash_register_id"]
                    )
                )

            except NotFoundException:

                raise NotFoundException(
                    "No se encontró la caja correspondiente al ID"
                )

            if not cash_register:

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

        # -----------------------------------------------------
        # ACTUALIZAR
        # -----------------------------------------------------

        return await self.repository.update(
            movement_id,
            update_data
        )