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
        # ESTADO ACTUAL
        # -----------------------------------------------------

        current_status = cash_register.get(
            "status_cash_register"
        )

        requested_status = data.status_cash_register

        # -----------------------------------------------------
        # NO PERMITIR REABRIR
        # -----------------------------------------------------

        if (
            current_status == "close"
            and requested_status == "open"
        ):

            raise NotFoundException(
                "Una caja cerrada no puede volver a abrirse."
            )

        # -----------------------------------------------------
        # NO PERMITIR CERRAR UNA CAJA YA CERRADA
        # -----------------------------------------------------

        if (
            current_status == "close"
            and requested_status == "close"
        ):

            raise NotFoundException(
                "La caja ya se encuentra cerrada."
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
                    "Debe indicar el efectivo contado "
                    "al cerrar la caja."
                )

            if closing_amount < 0:

                raise NotFoundException(
                    "El efectivo de cierre no puede ser negativo."
                )

            # -------------------------------------------------
            # OBTENER MOVIMIENTOS DE LA CAJA
            # -------------------------------------------------

            movements = (
                await self.cash_movement_repository
                .get_by_cash_register_id(
                    cash_register_id
                )
            )

            # =================================================
            # VARIABLES DEL RESUMEN
            # =================================================

            sales_total = 0

            sales_cash = 0

            sales_transfer = 0

            sales_qr = 0

            sales_debit_card = 0

            manual_income = 0

            manual_expense = 0

            manual_income_cash = 0

            manual_expense_cash = 0

            # =================================================
            # RECORRER MOVIMIENTOS
            # =================================================

            for movement in movements:

                amount = movement.get(
                    "amount",
                    0
                ) or 0

                movement_type = movement.get(
                    "type"
                )

                method_payment = movement.get(
                    "method_payment"
                )

                order_id = movement.get(
                    "order_id"
                )

                # =================================================
                # VENTA / COMANDA
                #
                # Una venta se identifica por tener order_id.
                # =================================================

                is_sale = bool(order_id)

                if is_sale:

                    # -------------------------------------------------
                    # SOLO LOS INFLOWS REPRESENTAN LA VENTA
                    # -------------------------------------------------

                    if movement_type != "inflow":
                        continue

                    sales_total += amount

                    # -------------------------------------------------
                    # VENTA EN EFECTIVO
                    # -------------------------------------------------

                    if method_payment == "cash":

                        sales_cash += amount

                    # -------------------------------------------------
                    # VENTA POR TRANSFERENCIA
                    # -------------------------------------------------

                    elif method_payment == "transfer":

                        sales_transfer += amount

                    # -------------------------------------------------
                    # VENTA POR QR
                    # -------------------------------------------------

                    elif method_payment == "qr":

                        sales_qr += amount

                    # -------------------------------------------------
                    # VENTA POR DÉBITO
                    # -------------------------------------------------

                    elif method_payment == "debit_card":

                        sales_debit_card += amount

                    continue

                # =================================================
                # MOVIMIENTO MANUAL
                #
                # No tiene order_id.
                # =================================================

                if movement_type == "inflow":

                    # -------------------------------------------------
                    # TOTAL GENERAL DE INGRESOS MANUALES
                    # -------------------------------------------------

                    manual_income += amount

                    # -------------------------------------------------
                    # INGRESO MANUAL EN EFECTIVO
                    # -------------------------------------------------

                    if method_payment == "cash":

                        manual_income_cash += amount

                elif movement_type == "outflow":

                    # -------------------------------------------------
                    # TOTAL GENERAL DE EGRESOS MANUALES
                    # -------------------------------------------------

                    manual_expense += amount

                    # -------------------------------------------------
                    # EGRESO MANUAL EN EFECTIVO
                    # -------------------------------------------------

                    if method_payment == "cash":

                        manual_expense_cash += amount

            # =====================================================
            # EFECTIVO ESPERADO
            #
            # SOLO DINERO FÍSICO:
            #
            # apertura
            # + ventas en efectivo
            # + ingresos manuales en efectivo
            # - egresos manuales en efectivo
            #
            # Transferencia, QR y débito NO afectan el efectivo.
            # =====================================================

            opening_amount = cash_register.get(
                "opening_amount",
                0
            ) or 0

            expected_amount = (
                opening_amount
                + sales_cash
                + manual_income_cash
                - manual_expense_cash
            )

            # =====================================================
            # DIFERENCIA
            #
            # Lo contado físicamente
            # menos lo que debería haber.
            # =====================================================

            difference = (
                closing_amount
                - expected_amount
            )

            # =====================================================
            # GUARDAR RESUMEN DE VENTAS
            # =====================================================

            update_data["sales_total"] = (
                sales_total
            )

            update_data["sales_cash"] = (
                sales_cash
            )

            update_data["sales_transfer"] = (
                sales_transfer
            )

            update_data["sales_qr"] = (
                sales_qr
            )

            update_data["sales_debit_card"] = (
                sales_debit_card
            )

            # =====================================================
            # GUARDAR RESUMEN DE MOVIMIENTOS MANUALES
            # =====================================================

            update_data["manual_income"] = (
                manual_income
            )

            update_data["manual_expense"] = (
                manual_expense
            )

            # =====================================================
            # GUARDAR SOLO LOS MOVIMIENTOS MANUALES
            # QUE AFECTARON EL EFECTIVO
            # =====================================================

            update_data["manual_income_cash"] = (
                manual_income_cash
            )

            update_data["manual_expense_cash"] = (
                manual_expense_cash
            )

            # =====================================================
            # GUARDAR EFECTIVO ESPERADO
            # =====================================================

            update_data["expected_amount"] = (
                expected_amount
            )

            # =====================================================
            # GUARDAR DIFERENCIA
            # =====================================================

            update_data["difference"] = (
                difference
            )

            # =====================================================
            # FECHA DE CIERRE
            # =====================================================

            if "closed_at" not in update_data:

                update_data["closed_at"] = (
                    DateUtils.now_argentina()
                )

        # =====================================================
        # CAMBIAR UNA CAJA ABIERTA
        # =====================================================

        if current_status == "open":

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

        # =====================================================
        # ACTUALIZAR
        # =====================================================

        return await self.repository.update(
            cash_register_id,
            update_data
        )