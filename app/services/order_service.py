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
    # PROCESAR PRODUCTOS
    # =========================================================

    async def _process_items(
        self,
        items,
        old_items=None
    ):

        if not items:

            raise NotFoundException(
                "No se puede crear una comanda sin productos"
            )

        old_items_map = {}

        if old_items:

            for old_item in old_items:

                product_id = str(
                    old_item["product_id"]
                )

                old_items_map[product_id] = (
                    old_items_map.get(product_id, 0)
                    + old_item["quantity"]
                )

        order_items = []

        total_price = 0

        for item in items:

            product = await self.product_repository.get_by_id(
                item.product_id
            )

            if not product:

                raise NotFoundException(
                    f"El producto con ID "
                    f"{item.product_id} no existe"
                )

            if not product["status"]:

                raise NotFoundException(
                    f"El producto '{product['name']}' "
                    f"está inactivo."
                )

            if item.quantity <= 0:

                raise NotFoundException(
                    "La cantidad del producto debe "
                    "ser mayor a 0"
                )

            product_id = str(
                item.product_id
            )

            old_quantity = old_items_map.get(
                product_id,
                0
            )

            # -------------------------------------------------
            # EN UNA EDICIÓN SOLO NECESITAMOS STOCK PARA
            # LA CANTIDAD QUE SE ESTÁ AGREGANDO.
            # -------------------------------------------------

            additional_quantity = (
                item.quantity - old_quantity
            )

            if additional_quantity > 0:

                if (
                    product["quantity"]
                    < additional_quantity
                ):

                    raise NotFoundException(
                        f"No hay stock suficiente "
                        f"del producto: {product['name']}. "
                        f"Disponible: {product['quantity']}, "
                        f"solicitado adicionalmente: "
                        f"{additional_quantity}"
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
    # VALIDAR CAJA
    # =========================================================

    async def _get_cash_register(
        self,
        cash_register_id: str
    ):

        cash_register = (
            await self.cash_register_repository.get_by_id(
                cash_register_id
            )
        )

        if not cash_register:

            raise NotFoundException(
                "No se encontró la caja indicada"
            )

        if not cash_register["status"]:

            raise NotFoundException(
                "La caja indicada está inactiva"
            )

        if (
            cash_register["status_cash_register"]
            != "open"
        ):

            raise NotFoundException(
                "La caja indicada está cerrada. "
                "No se pueden realizar movimientos "
                "sobre una caja cerrada."
            )

        return cash_register

    # =========================================================
    # CREAR ORDEN
    # =========================================================

    async def create(
        self,
        data
    ):

        # -----------------------------------------------------
        # NO PERMITIR CREAR DIRECTAMENTE CANCELADA
        # -----------------------------------------------------

        if data.status_payment == "cancelled":

            raise NotFoundException(
                "No se puede crear una orden "
                "directamente como cancelada"
            )

        # -----------------------------------------------------
        # PROCESAR PRODUCTOS
        # -----------------------------------------------------

        items, total_price = (
            await self._process_items(
                data.items
            )
        )

        # -----------------------------------------------------
        # TODA ORDEN DEBE TENER CAJA
        #
        # Como toda orden genera movimiento de caja,
        # incluso si amount = 0, necesita una caja abierta.
        # -----------------------------------------------------

        if not data.cash_register_id:

            raise NotFoundException(
                "Debe indicar una caja para crear "
                "la orden"
            )

        await self._get_cash_register(
            data.cash_register_id
        )

        # -----------------------------------------------------
        # DATOS DE LA ORDEN
        # -----------------------------------------------------

        date = DateUtils.now_argentina()

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

        await self._create_stock_outflows(
            order
        )

        # -----------------------------------------------------
        # TODA ORDEN GENERA MOVIMIENTO DE CAJA
        #
        # pending = 0
        # paid    = total
        # -----------------------------------------------------

        amount = (
            total_price
            if data.status_payment == "paid"
            else 0
        )

        await self._create_sale_cash_movement(
            order=order,
            amount=amount,
            method_payment=data.method_payment,
            cash_register_id=data.cash_register_id
        )

        return order

    # =========================================================
    # CREAR MOVIMIENTOS DE STOCK
    # =========================================================

    async def _create_stock_outflows(
        self,
        order
    ):

        for item in order["items"]:

            movement = StockMovementCreate(

                product_id=item["product_id"],

                type="outflow",

                description=(
                    f"Venta pedido "
                    f"#{order['order_number']}"
                ),

                quantity=item["quantity"],

                order_id=order["id"],

                status=True
            )

            await self.stock_movement_service.create(
                movement
            )

    # =========================================================
    # CREAR MOVIMIENTO DE VENTA
    # =========================================================

    async def _create_sale_cash_movement(
        self,
        order,
        amount,
        method_payment,
        cash_register_id
    ):

        cash_register = (
            await self._get_cash_register(
                cash_register_id
            )
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

            type="inflow",

            category="sale",

            amount=amount,

            method_payment=method_payment,

            description=(
                f"Venta pedido "
                f"#{order['order_number']}"
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

        old_payment_status = (
            old_order["status_payment"]
        )

        new_payment_status = (
            data.status_payment
            if data.status_payment is not None
            else old_payment_status
        )

        # =====================================================
        # CANCELADA NO PUEDE VOLVER ATRÁS
        # =====================================================

        if old_payment_status == "cancelled":

            if new_payment_status != "cancelled":

                raise NotFoundException(
                    "Una orden cancelada no puede volver "
                    "a cambiar su estado de pago"
                )

        # =====================================================
        # PAID -> PENDING
        # =====================================================

        if (
            old_payment_status == "paid"
            and new_payment_status == "pending"
        ):

            raise NotFoundException(
                "Una orden pagada no puede volver "
                "a pendiente"
            )

        # =====================================================
        # NO EDITAR ITEMS SI ESTÁ PAGADA O CANCELADA
        # =====================================================

        if data.items is not None:

            if old_payment_status == "paid":

                raise NotFoundException(
                    "No se pueden modificar los productos "
                    "de una orden pagada"
                )

            if old_payment_status == "cancelled":

                raise NotFoundException(
                    "No se pueden modificar los productos "
                    "de una orden cancelada"
                )

        # -----------------------------------------------------
        # DATOS A ACTUALIZAR
        # -----------------------------------------------------

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # =====================================================
        # DETERMINAR CAJA
        # =====================================================

        cash_register_id = (
            data.cash_register_id
            if data.cash_register_id is not None
            else old_order.get("cash_register_id")
        )

        # =====================================================
        # VALIDAR CAJA SI SE CAMBIA
        # =====================================================

        if data.cash_register_id is not None:

            await self._get_cash_register(
                data.cash_register_id
            )

        # =====================================================
        # EDITAR ITEMS
        # =====================================================

        if data.items is not None:

            new_items, new_total = (
                await self._process_items(
                    data.items,
                    old_items=old_order["items"]
                )
            )

            update_data["items"] = new_items

            update_data["total_price"] = new_total

            await self._adjust_order_stock(
                old_order["items"],
                new_items,
                old_order["id"]
            )

        # =====================================================
        # PENDING -> PAID
        # =====================================================

        if (
            old_payment_status == "pending"
            and new_payment_status == "paid"
        ):

            if not cash_register_id:

                raise NotFoundException(
                    "Debe indicar la caja para registrar "
                    "el pago"
                )

            await self._get_cash_register(
                cash_register_id
            )

            method_payment = (
                data.method_payment
                if data.method_payment is not None
                else old_order["method_payment"]
            )

            # -------------------------------------------------
            # ACTUALIZAR MOVIMIENTO EXISTENTE
            # DE $0 -> TOTAL
            # -------------------------------------------------

            await self.cash_movement_service.update_order_movement(
                order_id=str(old_order["id"]),
                amount=old_order["total_price"],
                method_payment=method_payment,
                cash_register_id=cash_register_id
            )

            update_data["cash_register_id"] = (
                cash_register_id
            )

        # =====================================================
        # PENDING -> CANCELLED
        # =====================================================

        if (
            old_payment_status == "pending"
            and new_payment_status == "cancelled"
        ):

            # El movimiento de caja original permanece
            # registrado con amount = 0.

            await self._restore_order_stock(
                old_order
            )

        # =====================================================
        # PAID -> CANCELLED
        # =====================================================

        if (
            old_payment_status == "paid"
            and new_payment_status == "cancelled"
        ):

            await self._refund_order(
                old_order,
                cash_register_id=data.cash_register_id
            )

        # =====================================================
        # ACTUALIZAR ORDEN
        # =====================================================

        return await self.repository.update(
            order_id,
            update_data
        )

    # =========================================================
    # AJUSTAR STOCK AL EDITAR ITEMS
    # =========================================================

    async def _adjust_order_stock(
        self,
        old_items,
        new_items,
        order_id
    ):

        old_map = {}

        new_map = {}

        # -----------------------------------------------------
        # STOCK ANTERIOR
        # -----------------------------------------------------

        for item in old_items:

            product_id = str(
                item["product_id"]
            )

            old_map[product_id] = (
                old_map.get(product_id, 0)
                + item["quantity"]
            )

        # -----------------------------------------------------
        # STOCK NUEVO
        # -----------------------------------------------------

        for item in new_items:

            product_id = str(
                item["product_id"]
            )

            new_map[product_id] = (
                new_map.get(product_id, 0)
                + item["quantity"]
            )

        # -----------------------------------------------------
        # PRODUCTOS AFECTADOS
        # -----------------------------------------------------

        product_ids = set(
            old_map.keys()
        ).union(
            new_map.keys()
        )

        for product_id in product_ids:

            old_quantity = old_map.get(
                product_id,
                0
            )

            new_quantity = new_map.get(
                product_id,
                0
            )

            difference = (
                new_quantity
                - old_quantity
            )

            # -------------------------------------------------
            # SE AGREGARON PRODUCTOS
            # -------------------------------------------------

            if difference > 0:

                movement = StockMovementCreate(

                    product_id=product_id,

                    type="outflow",

                    description=(
                        f"Agregado a pedido "
                        f"#{order_id}"
                    ),

                    quantity=difference,

                    order_id=order_id,

                    status=True
                )

                await self.stock_movement_service.create(
                    movement
                )

            # -------------------------------------------------
            # SE QUITARON PRODUCTOS
            # -------------------------------------------------

            elif difference < 0:

                movement = StockMovementCreate(

                    product_id=product_id,

                    type="inflow",

                    description=(
                        f"Quitado de pedido "
                        f"#{order_id}"
                    ),

                    quantity=abs(difference),

                    order_id=order_id,

                    status=True
                )

                await self.stock_movement_service.create(
                    movement
                )

    # =========================================================
    # REEMBOLSO
    # =========================================================

    async def _refund_order(
        self,
        order,
        cash_register_id=None
    ):

        # -----------------------------------------------------
        # SI SE ENVÍA UNA CAJA, USAR ESA.
        #
        # Esto permite devolver dinero desde la caja
        # actualmente abierta y no obliga a reabrir
        # la caja original.
        # -----------------------------------------------------

        selected_cash_register_id = (
            cash_register_id
            or order.get("cash_register_id")
        )

        if not selected_cash_register_id:

            raise NotFoundException(
                "Debe indicar una caja para realizar "
                "el reembolso"
            )

        cash_register = (
            await self._get_cash_register(
                selected_cash_register_id
            )
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
                f"Reembolso pedido "
                f"#{order['order_number']}"
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