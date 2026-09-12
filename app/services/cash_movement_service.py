from app.utils.dateZone import DateUtils

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
    # VALIDAR CAJA
    # =========================================================

    async def _get_cash_register(
        self,
        cash_register_id
    ):

        try:

            validate_object_id(
                cash_register_id
            )

            cash_register = (
                await self.cash_register_repository.get_by_id(
                    cash_register_id
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
                "No se pueden registrar movimientos "
                "en una caja cerrada"
            )

        return cash_register

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

        cash_register = (
            await self._get_cash_register(
                data.cash_register_id
            )
        )

        # -----------------------------------------------------
        # VALIDAR MONTO
        #
        # Movimiento manual:
        #       amount > 0
        #
        # Movimiento de orden:
        #       amount >= 0
        # -----------------------------------------------------

        if data.order_id:

            if data.amount < 0:

                raise NotFoundException(
                    "El valor no puede ser negativo"
                )

        else:

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
                    "No se encontró la orden correspondiente "
                    "al ID"
                )

            if not order:

                raise NotFoundException(
                    "No se encontró la orden correspondiente "
                    "al ID"
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
            # IMPORTANTE:
            #
            # NO reemplazamos amount por total_price.
            #
            # La orden puede tener:
            #
            # pending -> 0
            # paid    -> total
            # -------------------------------------------------

        # -----------------------------------------------------
        # PREPARAR MOVIMIENTO
        # -----------------------------------------------------

        movement_data = data.model_dump(
            exclude_none=True
        )

        movement_data["amount"] = amount

        if not movement_data.get("date"):

            movement_data["date"] = (
                DateUtils.now_argentina()
            )

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

        # -----------------------------------------------------
        # VALIDAR MONTO
        # -----------------------------------------------------

        if "amount" in update_data:

            if old.get("order_id"):

                if update_data["amount"] < 0:

                    raise NotFoundException(
                        "El valor no puede ser negativo"
                    )

            else:

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
                        "No se encontró la orden correspondiente "
                        "al ID"
                    )

                if not order:

                    raise NotFoundException(
                        "No se encontró la orden correspondiente "
                        "al ID"
                    )

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

        # =====================================================
        # VALIDAR CAJA
        # =====================================================

        if "cash_register_id" in update_data:

            await self._get_cash_register(
                update_data["cash_register_id"]
            )

        # -----------------------------------------------------
        # ACTUALIZAR
        # -----------------------------------------------------

        return await self.repository.update(
            movement_id,
            update_data
        )

    # =========================================================
    # ACTUALIZAR MOVIMIENTO DE UNA ORDEN
    # =========================================================

    async def update_order_movement(
        self,
        order_id,
        amount,
        method_payment,
        cash_register_id
    ):

        # -----------------------------------------------------
        # VALIDAR CAJA
        # -----------------------------------------------------

        cash_register = (
            await self._get_cash_register(
                cash_register_id
            )
        )

        # -----------------------------------------------------
        # VALIDAR ORDEN
        # -----------------------------------------------------

        try:

            validate_object_id(
                order_id
            )

            order = (
                await self.order_repository.get_by_id(
                    order_id
                )
            )

        except NotFoundException:

            raise NotFoundException(
                "No se encontró la orden correspondiente "
                "al ID"
            )

        if not order:

            raise NotFoundException(
                "No se encontró la orden correspondiente "
                "al ID"
            )

        # -----------------------------------------------------
        # VERIFICAR CAJA
        # -----------------------------------------------------

        order_cash_register_id = (
            order.get("cash_register_id")
        )

        if (
            order_cash_register_id
            and
            str(order_cash_register_id)
            != str(cash_register_id)
        ):

            raise NotFoundException(
                "La orden no pertenece "
                "a la caja seleccionada"
            )

        # -----------------------------------------------------
        # VALIDAR MONTO
        # -----------------------------------------------------

        if amount < 0:

            raise NotFoundException(
                "El valor no puede ser negativo"
            )

        # -----------------------------------------------------
        # BUSCAR MOVIMIENTO DE LA ORDEN
        # -----------------------------------------------------

        movement = (
            await self.repository.get_by_order_id(
                order_id
            )
        )

        if not movement:

            raise NotFoundException(
                "No se encontró el movimiento "
                "de la orden"
            )

        # -----------------------------------------------------
        # ACTUALIZAR MOVIMIENTO
        # -----------------------------------------------------

        update_data = {

            "amount": amount,

            "method_payment": method_payment,

            "cash_register_id": str(
                cash_register["id"]
            ),

            "description": (
                f"Venta pedido "
                f"#{order['order_number']}"
            )
        }

        return await self.repository.update(
            movement["id"],
            update_data
        )