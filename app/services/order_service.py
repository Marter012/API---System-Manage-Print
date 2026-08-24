from datetime import datetime

from app.services.base_service import BaseService

from app.services.stock_movement_service import (
    StockMovementService
)

from app.services.cash_movement_service import (
    CashMovementService
)

from app.repositories.order_repository import (
    OrderRepository
)

from app.repositories.product_repository import (
    ProductRepository
)

from app.repositories.cash_register_repository import (
    CashRegisterRepository
)

from app.schema.stock_movement_schema import (
    StockMovementCreate
)

from app.schema.cash_movement_schema import (
    CashMovementCreate
)

from app.schema.order_schema import (
    PAYMENT_PAID,
    PAYMENT_PENDING,
    PAYMENT_CANCELLED
)

from app.utils.exceptions import NotFoundException


class OrderService(BaseService):

    def __init__(self):

        self.repository = OrderRepository()

        self.product_repository = (
            ProductRepository()
        )

        self.stock_movement_service = (
            StockMovementService()
        )

        self.cash_movement_service = (
            CashMovementService()
        )

        self.cash_register_repository = (
            CashRegisterRepository()
        )

        super().__init__(
            self.repository
        )

    # =========================================================
    # PROCESS ITEMS
    # =========================================================

    async def _process_items(self, items):

        if not items:

            raise NotFoundException(
                "No se puede crear una comanda sin productos"
            )

        order_items = []

        total_price = 0

        for item in items:

            product = (
                await self.product_repository.get_by_id(
                    item.product_id
                )
            )

            if not product:

                raise NotFoundException(
                    f"El producto con ID "
                    f"{item.product_id} no existe"
                )

            if not product["status"]:

                raise NotFoundException(
                    f"El producto "
                    f"'{product['name']}' está inactivo."
                )

            if item.quantity <= 0:

                raise NotFoundException(
                    "La cantidad del producto "
                    "debe ser mayor a 0"
                )

            if product["quantity"] < item.quantity:

                raise NotFoundException(
                    f"No hay stock suficiente del producto: "
                    f"{product['name']}. "
                    f"Disponible: {product['quantity']}, "
                    f"solicitado: {item.quantity}"
                )

            unit_price = product["price"]

            subtotal = (
                unit_price * item.quantity
            )

            order_item = {

                "id": item.product_id,

                "product_id": item.product_id,

                "name": product["name"],

                "quantity": item.quantity,

                "unit_price": unit_price,

                "subtotal": subtotal,

                "status": True
            }

            order_items.append(
                order_item
            )

            total_price += subtotal

        return order_items, total_price

    # =========================================================
    # CREATE ORDER
    # =========================================================

    async def create(self, data):

        # -----------------------------------------------------
        # VALIDAR ESTADO DE PAGO
        # -----------------------------------------------------

        if data.status_payment not in [
            PAYMENT_PENDING,
            PAYMENT_PAID,
            PAYMENT_CANCELLED
        ]:

            raise NotFoundException(
                "Estado de pago no válido. "
                "Use: paid, pending o cancelled"
            )

        # -----------------------------------------------------
        # VALIDAR PRODUCTOS
        # -----------------------------------------------------

        items, total_price = (
            await self._process_items(
                data.items
            )
        )

        # -----------------------------------------------------
        # CREAR ORDER
        # -----------------------------------------------------

        order_data = {

            "order_number": data.order_number,

            "customer_name": data.customer_name,

            "items": items,

            "total_price": total_price,

            "method_payment": data.method_payment,

            "status_payment": data.status_payment,

            "created_at": datetime.now(),

            "delivery_time": data.delivery_time,

            "status": data.status
        }
        
        if data.status_payment == PAYMENT_PAID:

            cash_register = (
                await self.cash_register_repository
                .get_open_register()
            )

            if not cash_register:

                raise NotFoundException(
                    "No hay una caja abierta "
                    "para registrar una venta pagada"
                )

        order = await self.repository.create(
            order_data
        )

        # -----------------------------------------------------
        # STOCK
        # -----------------------------------------------------

        for item in items:

            movement = StockMovementCreate(

                product_id=item["product_id"],

                type="outflow",

                description=(
                    f"Venta pedido "
                    f"#{data.order_number}"
                ),

                quantity=item["quantity"],

                order_id=order["id"],

                status=True
            )

            await self.stock_movement_service.create(
                movement
            )

        # -----------------------------------------------------
        # CAJA
        # -----------------------------------------------------

        if data.status_payment == PAYMENT_PAID:

            await self._create_sale_cash_movement(
                order=order,
                total_price=total_price,
                method_payment=data.method_payment
            )

        return order

    # =========================================================
    # CREATE SALE CASH MOVEMENT
    # =========================================================

    async def _create_sale_cash_movement(
        self,
        order,
        total_price,
        method_payment
    ):

        cash_register = (
            await self.cash_register_repository
            .get_open_register()
        )

        if not cash_register:
            raise NotFoundException(
                "No hay una caja abierta "
                "para registrar el pago"
            )

        # ID caja
        cash_register_id = (
            cash_register.get("id")
            or cash_register.get("_id")
        )

        if not cash_register_id:
            raise NotFoundException(
                "La caja abierta no tiene un ID válido"
            )

        # ID orden
        order_id = (
            order.get("id")
            or order.get("_id")
        )

        if not order_id:
            raise NotFoundException(
                "La orden no tiene un ID válido"
            )

        cash_movement = CashMovementCreate(

            cash_register_id=str(cash_register_id),

            order_id=str(order_id),

            type="inflow",

            category="sale",

            amount=total_price,

            method_payment=method_payment,

            description=(
                f"Venta pedido "
                f"#{order['order_number']}"
            ),

            date=datetime.now(),

            status=True
        )

        return await self.cash_movement_service.create(
            cash_movement
        )

    # =========================================================
    # UPDATE ORDER
    # =========================================================

    async def update(
        self,
        order_id,
        data
    ):

        # -----------------------------------------------------
        # BUSCAR ORDEN ACTUAL
        # -----------------------------------------------------

        old_order = await self.repository.get_by_id(
            order_id
        )

        if not old_order:

            raise NotFoundException(
                "Orden no encontrada"
            )

        # -----------------------------------------------------
        # VALIDAR NUEVO ESTADO
        # -----------------------------------------------------

        if data.status_payment is not None:

            if data.status_payment not in [
                PAYMENT_PENDING,
                PAYMENT_PAID,
                PAYMENT_CANCELLED
            ]:

                raise NotFoundException(
                    "Estado de pago no válido. "
                    "Use: paid, pending o cancelled"
                )

        old_payment_status = (
            old_order["status_payment"]
        )

        new_payment_status = (
            data.status_payment
            if data.status_payment is not None
            else old_payment_status
        )
        
        if old_payment_status == PAYMENT_CANCELLED:

            if new_payment_status != PAYMENT_CANCELLED:

                raise NotFoundException(
                    "Una orden cancelada no puede "
                    "volver a cambiar su estado de pago"
                )

        # -----------------------------------------------------
        # NO PERMITIR MODIFICAR ITEMS
        # -----------------------------------------------------

        if data.items is not None:

            raise NotFoundException(
                "No se pueden modificar los productos "
                "de una orden mediante este endpoint. "
                "Esto requiere recalcular los movimientos "
                "de stock."
            )

        # -----------------------------------------------------
        # PREPARAR UPDATE
        # -----------------------------------------------------

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # -----------------------------------------------------
        # PENDING -> PAID
        # -----------------------------------------------------

        if (
            old_payment_status == PAYMENT_PENDING
            and new_payment_status == PAYMENT_PAID
        ):

            await self._create_sale_cash_movement(
                order=old_order,
                total_price=old_order["total_price"],
                method_payment=(
                    data.method_payment
                    if data.method_payment is not None
                    else old_order["method_payment"]
                )
            )

        # -----------------------------------------------------
        # PAID -> CANCELLED
        # -----------------------------------------------------

        if (
            old_payment_status == PAYMENT_PAID
            and new_payment_status == PAYMENT_CANCELLED
        ):

            await self._refund_order(
                old_order
            )

        # -----------------------------------------------------
        # PENDING -> CANCELLED
        # -----------------------------------------------------

        if (
            old_payment_status == PAYMENT_PENDING
            and new_payment_status == PAYMENT_CANCELLED
        ):

            await self._restore_order_stock(
                old_order
            )

        # -----------------------------------------------------
        # ACTUALIZAR ORDER
        # -----------------------------------------------------

        return await self.repository.update(
            order_id,
            update_data
        )

    # =========================================================
    # REFUND ORDER
    # =========================================================

    async def _refund_order(
        self,
        order
    ):

        cash_register = (
            await self.cash_register_repository
            .get_open_register()
        )

        if not cash_register:

            raise NotFoundException(
                "No hay una caja abierta "
                "para registrar el reembolso"
            )

        cash_movement = CashMovementCreate(

            cash_register_id=cash_register["id"],

            order_id=order["id"],

            type="outflow",

            category="refund",

            amount=order["total_price"],

            method_payment=order["method_payment"],

            description=(
                f"Reembolso pedido "
                f"#{order['order_number']}"
            ),

            date=datetime.now(),

            status=True
        )

        await self.cash_movement_service.create(
            cash_movement
        )

        # Devolver productos al stock
        await self._restore_order_stock(
            order
        )

    # =========================================================
    # RESTORE ORDER STOCK
    # =========================================================

    async def _restore_order_stock(
        self,
        order
    ):

        for item in order["items"]:

            movement = StockMovementCreate(

                product_id=item["product_id"],

                type="inflow",

                description=(
                    f"Devolución pedido "
                    f"#{order['order_number']}"
                ),

                quantity=item["quantity"],

                order_id=order["id"],

                status=True
            )

            await self.stock_movement_service.create(
                movement
            )