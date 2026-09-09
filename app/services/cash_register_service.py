from app.utils.dateZone import DateUtils

from app.services.base_service import BaseService

from app.repositories.cash_register_repository import (
    CashRegisterRepository
)

from app.repositories.cash_movement_repository import (
    CashMovementRepository
)

from app.utils.exceptions import NotFoundException


class CashRegisterService(BaseService):

    def __init__(self):

        self.repository = CashRegisterRepository()

        self.cash_movement_repository = CashMovementRepository()

        super().__init__(
            self.repository
        )

    # =========================================================
    # CREAR CAJA
    # =========================================================

    async def create(self, data):

        # -----------------------------------------------------
        # VALIDAR TURNO
        # -----------------------------------------------------

        if data.shift not in [
            "morning",
            "night"
        ]:

            raise NotFoundException(
                "Turno no válido. Use: morning o night"
            )

        # -----------------------------------------------------
        # VALIDAR MONTO DE APERTURA
        # -----------------------------------------------------

        if data.opening_amount < 0:

            raise NotFoundException(
                "El monto de apertura no puede ser negativo."
            )

        # -----------------------------------------------------
        # VALIDAR QUE NO EXISTA OTRA CAJA ABIERTA
        #
        # Solo puede existir UNA caja abierta en todo el sistema.
        #
        # Ejemplo:
        #
        # 08/09/2026 - morning → abierta
        #
        # Intentar:
        #
        # 09/09/2026 - morning → ❌
        # 09/09/2026 - night   → ❌
        #
        # Primero hay que cerrar la caja anterior.
        # -----------------------------------------------------

        open_cash_register = (
            await self.repository.get_open_register()
        )

        if open_cash_register:

            open_date = open_cash_register.get(
                "date",
                "desconocida"
            )

            open_shift = open_cash_register.get(
                "shift",
                "desconocido"
            )

            open_id = open_cash_register.get(
                "id",
                open_cash_register.get(
                    "_id",
                    "desconocido"
                )
            )

            raise NotFoundException(
                "No se puede abrir una nueva caja porque "
                "existe una caja abierta. "
                f"Fecha: {open_date}. "
                f"Turno: {open_shift}. "
                f"ID: {open_id}. "
                "Debe cerrar la caja anterior antes "
                "de abrir una nueva."
            )

        # -----------------------------------------------------
        # VALIDAR DUPLICADO DE FECHA + TURNO
        #
        # Esta validación sigue siendo necesaria aunque la caja
        # anterior esté cerrada.
        #
        # No permitimos dos registros para:
        #
        # misma fecha + mismo turno
        # -----------------------------------------------------

        existing_cash_register = (
            await self.repository.get_by_date_and_shift(
                data.date,
                data.shift
            )
        )

        if existing_cash_register:

            existing_status = (
                existing_cash_register.get(
                    "status_cash_register"
                )
            )

            if existing_status == "open":

                existing_id = (
                    existing_cash_register.get(
                        "id",
                        existing_cash_register.get(
                            "_id",
                            "desconocido"
                        )
                    )
                )

                raise NotFoundException(
                    f"La caja del día {data.date} "
                    f"del turno {data.shift} ya se encuentra "
                    f"abierta. ID: {existing_id}."
                )

            raise NotFoundException(
                f"Ya existe una caja registrada para el día "
                f"{data.date} del turno {data.shift}."
            )

        # -----------------------------------------------------
        # CREAR CAJA
        # -----------------------------------------------------

        cash_register_data = data.model_dump(
            exclude_none=True
        )

        return await self.repository.create(
            cash_register_data
        )

    # =========================================================
    # ACTUALIZAR CAJA
    # =========================================================

    async def update(
        self,
        cash_register_id,
        data
    ):

        # -----------------------------------------------------
        # BUSCAR CAJA
        # -----------------------------------------------------

        cash_register = (
            await self.repository.get_by_id(
                cash_register_id
            )
        )

        if not cash_register:

            raise NotFoundException(
                "Caja no encontrada"
            )

        # -----------------------------------------------------
        # NO PERMITIR REABRIR UNA CAJA CERRADA
        # -----------------------------------------------------

        current_status = cash_register.get(
            "status_cash_register"
        )

        requested_status = data.status_cash_register

        if (
            current_status == "close"
            and requested_status == "open"
        ):

            raise NotFoundException(
                "Una caja cerrada no puede volver a abrirse."
            )

        # -----------------------------------------------------
        # PREPARAR ACTUALIZACIÓN
        # -----------------------------------------------------

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # -----------------------------------------------------
        # VALIDAR TURNO
        # -----------------------------------------------------

        if "shift" in update_data:

            if update_data["shift"] not in [
                "morning",
                "night"
            ]:

                raise NotFoundException(
                    "Turno no válido. "
                    "Use: morning o night"
                )

        # -----------------------------------------------------
        # VALIDAR MONTO DE APERTURA
        # -----------------------------------------------------

        if "opening_amount" in update_data:

            if update_data["opening_amount"] < 0:

                raise NotFoundException(
                    "El monto de apertura no puede ser negativo."
                )

        # -----------------------------------------------------
        # DETERMINAR ESTADO FINAL
        # -----------------------------------------------------

        status_cash_register = update_data.get(
            "status_cash_register",
            current_status
        )

        # =====================================================
        # CERRAR CAJA
        # =====================================================

        if status_cash_register == "close":

            # -------------------------------------------------
            # VALIDAR MONTO DE CIERRE
            # -------------------------------------------------

            closing_amount = update_data.get(
                "closing_amount"
            )

            if closing_amount is None:

                raise NotFoundException(
                    "Debe indicar el monto de cierre de la caja."
                )

            if closing_amount < 0:

                raise NotFoundException(
                    "El monto de cierre no puede ser negativo."
                )

            # -------------------------------------------------
            # OBTENER MOVIMIENTOS
            # -------------------------------------------------

            movements = (
                await self.cash_movement_repository
                .get_by_cash_register_id(
                    cash_register_id
                )
            )

            # -------------------------------------------------
            # CALCULAR EFECTIVO ESPERADO
            #
            # IMPORTANTE:
            #
            # Solo los movimientos en efectivo afectan el
            # efectivo físico de la caja.
            #
            # QR
            # Transferencia
            # Débito
            # Mercado Pago
            #
            # NO se suman al efectivo esperado.
            # -------------------------------------------------

            opening_amount = cash_register.get(
                "opening_amount",
                0
            )

            expected_amount = opening_amount

            for movement in movements:

                method_payment = movement.get(
                    "method_payment"
                )

                # Solo efectivo modifica el efectivo físico.

                if method_payment != "cash":
                    continue

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
            # CALCULAR DIFERENCIA
            # -------------------------------------------------

            difference = (
                closing_amount
                - expected_amount
            )

            update_data["expected_amount"] = (
                expected_amount
            )

            update_data["difference"] = (
                difference
            )

            # -------------------------------------------------
            # FECHA DE CIERRE
            # -------------------------------------------------

            if "closed_at" not in update_data:

                update_data["closed_at"] = (
                    DateUtils.now_argentina()
                )

        # =====================================================
        # CAMBIAR UNA CAJA ABIERTA
        # =====================================================

        if current_status == "open":

            # Si se intenta cambiar la fecha o turno de una
            # caja abierta, verificamos que no genere conflictos.

            new_date = update_data.get(
                "date",
                cash_register.get("date")
            )

            new_shift = update_data.get(
                "shift",
                cash_register.get("shift")
            )

            # -------------------------------------------------
            # SI CAMBIA FECHA O TURNO
            # -------------------------------------------------

            if (
                new_date != cash_register.get("date")
                or new_shift != cash_register.get("shift")
            ):

                existing_cash_register = (
                    await self.repository
                    .get_by_date_and_shift(
                        new_date,
                        new_shift
                    )
                )

                if (
                    existing_cash_register
                    and existing_cash_register.get("id")
                    != cash_register_id
                ):

                    raise NotFoundException(
                        f"Ya existe una caja registrada "
                        f"para el día {new_date} "
                        f"del turno {new_shift}."
                    )

        # -----------------------------------------------------
        # ACTUALIZAR
        # -----------------------------------------------------

        return await self.repository.update(
            cash_register_id,
            update_data
        )
