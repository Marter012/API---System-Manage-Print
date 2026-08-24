from app.services.base_service import BaseService

from app.repositories.cash_register_repository import (
    CashRegisterRepository
)

from app.repositories.cash_movement_repository import (
    CashMovementRepository
)

from app.utils.exceptions import NotFoundException

from datetime import datetime


class CashRegisterService(BaseService):

    def __init__(self):

        self.repository = CashRegisterRepository()

        self.cash_movement_repository = (
            CashMovementRepository()
        )

        super().__init__(self.repository)

    # =========================================================
    # CREATE
    # =========================================================

    async def create(self, data):

        cash_registers = await self.repository.get_all()

        for cash in cash_registers:

            if cash["opened_at"].date() == data.opened_at.date():

                if cash["status_cash_register"] == "open":

                    raise NotFoundException(
                        f"La caja del día "
                        f"{data.opened_at.date()} "
                        "ya se encuentra abierta."
                    )

                raise NotFoundException(
                    f"Ya existe una caja registrada "
                    f"para el día {data.opened_at.date()}."
                )

        return await self.repository.create(
            data.model_dump(
                exclude_none=True
            )
        )

    # =========================================================
    # UPDATE
    # =========================================================

    async def update(
        self,
        cash_register_id,
        data
    ):

        # -----------------------------------------------------
        # Obtener caja actual
        # -----------------------------------------------------

        cash_register = await self.repository.get_by_id(
            cash_register_id
        )

        if not cash_register:

            raise NotFoundException(
                "Caja no encontrada"
            )

        # -----------------------------------------------------
        # Datos enviados
        # -----------------------------------------------------

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # -----------------------------------------------------
        # Si estamos cerrando la caja
        # -----------------------------------------------------

        status_cash_register = update_data.get(
            "status_cash_register",
            cash_register["status_cash_register"]
        )

        if status_cash_register == "close":

            # -------------------------------------------------
            # Debemos tener monto de cierre
            # -------------------------------------------------

            closing_amount = update_data.get(
                "closing_amount"
            )

            if closing_amount is None:

                raise NotFoundException(
                    "Debe indicar el monto de cierre "
                    "de la caja."
                )

            if closing_amount < 0:

                raise NotFoundException(
                    "El monto de cierre no puede ser negativo."
                )

            # -------------------------------------------------
            # Obtener movimientos de esta caja
            # -------------------------------------------------

            movements = (
                await self.cash_movement_repository
                .get_by_cash_register_id(
                    cash_register_id
                )
            )

            # -------------------------------------------------
            # Monto inicial
            # -------------------------------------------------

            opening_amount = cash_register.get(
                "opening_amount",
                0
            )

            expected_amount = opening_amount

            # -------------------------------------------------
            # Calcular movimientos
            # -------------------------------------------------

            for movement in movements:

                amount = movement.get(
                    "amount",
                    0
                )

                movement_type = movement.get(
                    "type"
                )

                if movement_type == "inflow":

                    expected_amount += amount

                elif movement_type == "outflow":

                    expected_amount -= amount

            # -------------------------------------------------
            # Diferencia
            # -------------------------------------------------

            difference = (
                closing_amount
                - expected_amount
            )

            # -------------------------------------------------
            # Guardar resultados
            # -------------------------------------------------

            update_data["expected_amount"] = (
                expected_amount
            )

            update_data["difference"] = (
                difference
            )

            # Si no mandaron closed_at
            # lo generamos automáticamente.

            if "closed_at" not in update_data:

                update_data["closed_at"] = datetime.now()

        # -----------------------------------------------------
        # Actualizar caja
        # -----------------------------------------------------

        return await self.repository.update(
            cash_register_id,
            update_data
        )