from app.utils.dateZone import DateUtils

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

from app.utils.exceptions import NotFoundException


class OrderService(BaseService):

    def __init__(self):

        self.repository = OrderRepository()

        self.product_repository = ProductRepository()

        self.stock_movement_service = StockMovementService()

        self.cash_movement_service = CashMovementService()

        self.cash_register_repository = CashRegisterRepository()

        super().__init__(self.repository)

    # =========================================================
    # PROCESAR PRODUCTOS DE LA ORDEN
    # =========================================================

    async def _process_items(self, items):

        if not items:
            raise NotFoundException(
                "No se puede crear una comanda sin productos"
            )

        order_items = []

        total_price = 0

        for item in items:

            product = await self.product_repository.get_by_id(
                item.product_id
            )

            if not product:
                raise NotFoundException(
                    f"El producto con ID {item.product_id} no existe"
                )

            if not product["status"]:
                raise NotFoundException(
                    f"El producto '{product['name']}' está inactivo."
                )

            if item.quantity <= 0:
                raise NotFoundException(
                    "La cantidad del producto debe ser mayor a 0"
                )

            if product["quantity"] < item.quantity:
                raise NotFoundException(
                    f"No hay stock suficiente del producto: "
                    f"{product['name']}. "
                    f"Disponible: {product['quantity']}, "
                    f"solicitado: {item.quantity}"
                )

            unit_price = product["price"]

            subtotal = unit_price * item.quantity

            order_item = {
                "id": item.product_id,
                "product_id": item.product_id,
                "name": product["name"],
                "quantity": item.quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "status": True
            }

            order_items.append(order_item)

            total_price += subtotal

        return order_items, total_price

    # =========================================================
    # VALIDAR CAJA
    # =========================================================

    async def _get_cash_register(
        self,
        cash_register_id: str
    ):

        cash_register = await self.cash_register_repository.get_by_id(
            cash_register_id
        )

        if not cash_register:
            raise NotFoundException(
                "No se encontró la caja indicada"
            )

        if not cash_register["status"]:
            raise NotFoundException(
                "La caja indicada está inactiva"
            )

        if cash_register["status_cash_register"] != "open":
            raise NotFoundException(
                "La caja indicada está cerrada. "
                "No se pueden crear órdenes asociadas a una caja cerrada."
            )

        return cash_register

    # =========================================================
    # CREAR ORDEN
    # =========================================================

    async def create(self, data):

        # -----------------------------------------------------
        # PROCESAR PRODUCTOS
        # -----------------------------------------------------

        items, total_price = await self._process_items(
            data.items
        )

        # -----------------------------------------------------
        # VALIDAR CAJA
        #
        # Si la orden tiene una caja asociada, la caja SIEMPRE
        # debe estar abierta.
        #
        # Esto aplica tanto para:
        #
        # pending
        # paid
        #
        # -----------------------------------------------------

        if data.cash_register_id:

            await self._get_cash_register(
                data.cash_register_id
            )

        # -----------------------------------------------------
        # SI LA ORDEN ESTÁ PAGADA
        #
        # Debe tener obligatoriamente una caja.
        # -----------------------------------------------------

        if data.status_payment == "paid":

            if not data.cash_register_id:

                raise NotFoundException(
                    "Debe indicar la caja para registrar "
                    "una venta pagada"
                )

            # Volvemos a validar explícitamente la caja
            # antes de registrar el movimiento.

            await self._get_cash_register(
                data.cash_register_id
            )

        # -----------------------------------------------------
        # DATOS DE LA ORDEN
        # -----------------------------------------------------
        date = DateUtils.now_argentina()

        print("FECHA ARGENTINA:", date)
        print("TIMEZONE:", date.tzinfo)
        order_data = {
            "order_number": data.order_number,
            "customer_name": data.customer_name,
            "items": items,
            "total_price": total_price,
            "method_payment": data.method_payment,
            "status_payment": data.status_payment,
            "created_at": date,
            "delivery_time": data.delivery_time,
            "cash_register_id": data.cash_register_id,
            "status": data.status
        }

        # -----------------------------------------------------
        # CREAR ORDEN
        # -----------------------------------------------------
        order = await self.repository.create(
            order_data
        )
        # -----------------------------------------------------
        # DESCONTAR STOCK
        # -----------------------------------------------------

        for item in items:

            movement = StockMovementCreate(
                product_id=item["product_id"],
                type="outflow",
                description=(
                    f"Venta pedido #{data.order_number}"
                ),
                quantity=item["quantity"],
                order_id=order["id"],
                status=True
            )

            await self.stock_movement_service.create(
                movement
            )

        # -----------------------------------------------------
        # SI ESTÁ PAGADA
        #
        # CREAR MOVIMIENTO DE CAJA
        # -----------------------------------------------------

        if data.status_payment == "paid":

            await self._create_sale_cash_movement(
                order=order,
                total_price=total_price,
                method_payment=data.method_payment,
                cash_register_id=data.cash_register_id
            )

        return order

    # =========================================================
    # CREAR MOVIMIENTO DE VENTA
    # =========================================================

    async def _create_sale_cash_movement(
        self,
        order,
        total_price,
        method_payment,
        cash_register_id
    ):

        # -----------------------------------------------------
        # VALIDAR NUEVAMENTE QUE LA CAJA ESTÉ ABIERTA
        # -----------------------------------------------------

        cash_register = await self._get_cash_register(
            cash_register_id
        )

        # -----------------------------------------------------
        # OBTENER ID DE LA ORDEN
        # -----------------------------------------------------

        order_id = (
            order.get("id")
            or order.get("_id")
        )

        if not order_id:

            raise NotFoundException(
                "La orden no tiene un ID válido"
            )

        # -----------------------------------------------------
        # CREAR MOVIMIENTO
        # -----------------------------------------------------

        cash_movement = CashMovementCreate(
            cash_register_id=str(
                cash_register["id"]
            ),

            order_id=str(
                order_id
            ),

            type="inflow",

            category="sale",

            amount=total_price,

            method_payment=method_payment,

            description=(
                f"Venta pedido #{order['order_number']}"
            ),

            date=DateUtils.now_argentina(),

            status=True
        )

        return await self.cash_movement_service.create(
            cash_movement
        )

    # =========================================================
    # ACTUALIZAR ORDEN
    # =========================================================

    async def update(
        self,
        order_id,
        data
    ):

        old_order = await self.repository.get_by_id(
            order_id
        )

        if not old_order:

            raise NotFoundException(
                "Orden no encontrada"
            )

        old_payment_status = old_order[
            "status_payment"
        ]

        new_payment_status = (
            data.status_payment
            if data.status_payment is not None
            else old_payment_status
        )

        # -----------------------------------------------------
        # UNA ORDEN CANCELADA NO PUEDE VOLVER ATRÁS
        # -----------------------------------------------------

        if old_payment_status == "cancelled":

            if new_payment_status != "cancelled":

                raise NotFoundException(
                    "Una orden cancelada no puede volver "
                    "a cambiar su estado de pago"
                )

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # -----------------------------------------------------
        # DETERMINAR CAJA
        # -----------------------------------------------------

        cash_register_id = (
            data.cash_register_id
            if data.cash_register_id is not None
            else old_order.get("cash_register_id")
        )

        # -----------------------------------------------------
        # SI SE ESTÁ ASOCIANDO UNA CAJA
        #
        # SIEMPRE DEBE ESTAR ABIERTA
        # -----------------------------------------------------

        if data.cash_register_id is not None:

            await self._get_cash_register(
                data.cash_register_id
            )

        # -----------------------------------------------------
        # PENDING -> PAID
        # -----------------------------------------------------

        if (
            old_payment_status == "pending"
            and new_payment_status == "paid"
        ):

            if not cash_register_id:

                raise NotFoundException(
                    "Debe indicar la caja para registrar "
                    "el pago"
                )

            # Verificar que la caja esté abierta.

            await self._get_cash_register(
                cash_register_id
            )

            method_payment = (
                data.method_payment
                if data.method_payment is not None
                else old_order["method_payment"]
            )

            # Crear movimiento de caja.

            await self._create_sale_cash_movement(
                order=old_order,
                total_price=old_order["total_price"],
                method_payment=method_payment,
                cash_register_id=cash_register_id
            )

            update_data["cash_register_id"] = (
                cash_register_id
            )

        # -----------------------------------------------------
        # PAID -> CANCELLED
        # -----------------------------------------------------

        if (
            old_payment_status == "paid"
            and new_payment_status == "cancelled"
        ):

            await self._refund_order(
                old_order
            )

        # -----------------------------------------------------
        # PENDING -> CANCELLED
        # -----------------------------------------------------

        if (
            old_payment_status == "pending"
            and new_payment_status == "cancelled"
        ):

            await self._restore_order_stock(
                old_order
            )

        # -----------------------------------------------------
        # ACTUALIZAR ORDEN
        # -----------------------------------------------------

        return await self.repository.update(
            order_id,
            update_data
        )

    # =========================================================
    # REEMBOLSO
    # =========================================================

    async def _refund_order(
        self,
        order
    ):

        cash_register_id = order.get(
            "cash_register_id"
        )

        if not cash_register_id:

            raise NotFoundException(
                "La orden no tiene una caja asociada"
            )

        # -----------------------------------------------------
        # EL REEMBOLSO TAMBIÉN NECESITA UNA CAJA ABIERTA
        # -----------------------------------------------------

        cash_register = await self._get_cash_register(
            cash_register_id
        )

        order_id = (
            order.get("id")
            or order.get("_id")
        )

        if not order_id:

            raise NotFoundException(
                "La orden no tiene un ID válido"
            )

        cash_movement = CashMovementCreate(
            cash_register_id=str(
                cash_register["id"]
            ),

            order_id=str(
                order_id
            ),

            type="outflow",

            category="refund",

            amount=order["total_price"],

            method_payment=order["method_payment"],

            description=(
                f"Reembolso pedido #{order['order_number']}"
            ),

            date=DateUtils.now_argentina(),

            status=True
        )

        await self.cash_movement_service.create(
            cash_movement
        )

        # -----------------------------------------------------
        # DEVOLVER STOCK
        # -----------------------------------------------------

        await self._restore_order_stock(
            order
        )

    # =========================================================
    # RESTAURAR STOCK
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
