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

from app.database.connection import database

from app.repositories.base_repository import BaseRepository

from app.schema.stock_movement_schema import (
    StockMovementCreate
)

from app.schema.cash_movement_schema import (
    CashMovementCreate
)

from app.utils.exceptions import NotFoundException


class PromotionRepository(BaseRepository):
    """
    Repositorio local para promociones.
    """

    def __init__(self):
        self.collection = database["promotions"]
        super().__init__(self.collection)

    async def get_by_id(self, promotion_id):
        return await super().get_by_id(promotion_id)


class OrderService(BaseService):

    def __init__(self):

        self.repository = OrderRepository()

        self.product_repository = ProductRepository()

        self.stock_movement_service = StockMovementService()

        self.cash_movement_service = CashMovementService()

        self.cash_register_repository = CashRegisterRepository()

        self.promotion_repository = PromotionRepository()

        super().__init__(self.repository)

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _value(item, name, default=None):

        if isinstance(item, dict):
            return item.get(name, default)

        return getattr(item, name, default)

    @staticmethod
    def _is_promotion_item(item):

        return bool(
            OrderService._value(item, "promotion_id")
            or OrderService._value(item, "type") == "promotion"
            or OrderService._value(item, "item_type") == "promotion"
        )

    def _normalize_promotion_selections(self, item):

        selections = self._value(
            item,
            "promotion_selections"
        )

        if selections is None:
            selections = self._value(
                item,
                "promotion_items"
            )

        if selections is None:
            selections = self._value(
                item,
                "selections"
            )

        if selections is None:
            selections = self._value(
                item,
                "items"
            )

        return selections or []

    @staticmethod
    def _selection_value(
        selection,
        name,
        default=None
    ):

        if isinstance(selection, dict):
            return selection.get(
                name,
                default
            )

        return getattr(
            selection,
            name,
            default
        )

    # =========================================================
    # VALIDAR SELECCIÓN DE PROMOCIÓN
    # =========================================================

    async def _validate_promotion_selection(
        self,
        promotion,
        selections,
        quantity=1,
        old_promotion_item=None
    ):
        """
        Valida la composición de una promoción.

        IMPORTANTE:

        promotion.quantity = cantidad de promociones vendidas.

        selection.quantity = cantidad de productos que contiene
        UNA promoción.

        Ejemplo:

        Promoción:
            12 empanadas

        Orden:
            quantity = 1

        Selección:
            quantity = 12

        Stock utilizado:
            12

        Si se venden 2 promociones:

            quantity = 2
            selección = 12

        Stock utilizado:
            12 * 2 = 24
        """

        template_items = (
            promotion.get("items")
            or promotion.get("composition")
            or []
        )

        if not template_items:

            raise NotFoundException(
                "La promoción no tiene una composición configurada"
            )

        if not selections:

            raise NotFoundException(
                "Debe indicar la composición elegida para la promoción"
            )

        # -----------------------------------------------------
        # AGRUPAR SELECCIONES
        # -----------------------------------------------------

        grouped = {}

        ungrouped = []

        for selection in selections:

            group_index = self._selection_value(
                selection,
                "group_index"
            )

            if group_index is None:

                group_index = self._selection_value(
                    selection,
                    "composition_index"
                )

            if group_index is None:

                ungrouped.append(selection)

            else:

                grouped.setdefault(
                    int(group_index),
                    []
                ).append(selection)

        normalized = []

        # -----------------------------------------------------
        # VALIDAR CADA GRUPO
        # -----------------------------------------------------

        for index, rule in enumerate(template_items):

            required = int(
                rule.get(
                    "quantity",
                    0
                )
            )

            if required <= 0:

                raise NotFoundException(
                    "La composición de la promoción tiene "
                    f"una cantidad inválida en el grupo {index}"
                )

            group = grouped.get(index)

            # -------------------------------------------------
            # SI NO VIENE group_index
            # -------------------------------------------------

            if group is None:

                remaining = required

                group = []

                while ungrouped and remaining > 0:

                    candidate = ungrouped[0]

                    candidate_quantity = int(
                        self._selection_value(
                            candidate,
                            "quantity",
                            0
                        )
                    )

                    if candidate_quantity <= 0:

                        raise NotFoundException(
                            "La cantidad seleccionada en una "
                            "promoción debe ser mayor a 0"
                        )

                    take = min(
                        candidate_quantity,
                        remaining
                    )

                    if take == candidate_quantity:

                        group.append(
                            ungrouped.pop(0)
                        )

                    else:

                        if isinstance(candidate, dict):

                            part = dict(candidate)

                        else:

                            part = {
                                "product_id":
                                    self._selection_value(
                                        candidate,
                                        "product_id"
                                    ),
                                "quantity": take
                            }

                        part["quantity"] = take

                        group.append(part)

                        if isinstance(candidate, dict):

                            candidate["quantity"] = (
                                candidate_quantity - take
                            )

                    remaining -= take

                if remaining > 0:

                    raise NotFoundException(
                        f"La promoción "
                        f"'{promotion.get('name', 'sin nombre')}' "
                        f"requiere {required} unidades "
                        f"en el grupo {index}"
                    )

            # -------------------------------------------------
            # VALIDAR PRODUCTOS DEL GRUPO
            # -------------------------------------------------

            group_total = 0

            allowed_ids = {
                str(x)
                for x in (
                    rule.get("product_ids")
                    or rule.get("allowed_product_ids")
                    or []
                )
            }

            fixed_product_id = rule.get(
                "product_id"
            )

            allowed_category = rule.get(
                "category"
            )

            for selection in group:

                product_id = self._selection_value(
                    selection,
                    "product_id"
                )

                selection_quantity = int(
                    self._selection_value(
                        selection,
                        "quantity",
                        0
                    )
                )

                if (
                    not product_id
                    or selection_quantity <= 0
                ):

                    raise NotFoundException(
                        "Cada selección de una promoción debe "
                        "indicar producto y cantidad válida"
                    )

                product = await self.product_repository.get_by_id(
                    product_id
                )

                if not product:

                    raise NotFoundException(
                        f"El producto con ID "
                        f"{product_id} no existe"
                    )

                if not product["status"]:

                    raise NotFoundException(
                        f"El producto '{product['name']}' "
                        "está inactivo"
                    )

                if (
                    fixed_product_id
                    and str(fixed_product_id)
                    != str(product_id)
                ):

                    raise NotFoundException(
                        f"El producto '{product['name']}' "
                        "no corresponde al grupo fijo "
                        "de la promoción"
                    )

                if (
                    allowed_ids
                    and str(product_id)
                    not in allowed_ids
                ):

                    raise NotFoundException(
                        f"El producto '{product['name']}' "
                        "no está permitido en este grupo "
                        "de la promoción"
                    )

                if (
                    allowed_category
                    and str(
                        product.get(
                            "category",
                            ""
                        )
                    ).lower()
                    != str(
                        allowed_category
                    ).lower()
                ):

                    raise NotFoundException(
                        f"El producto '{product['name']}' "
                        "no pertenece a la categoría permitida"
                    )

                group_total += selection_quantity

                normalized.append({
                    "group_index": index,
                    "product_id": product_id,
                    "name": product["name"],
                    "quantity": selection_quantity,
                    "unit_price": product["price"],
                    "subtotal":
                        product["price"]
                        * selection_quantity,
                    "status": True
                })

            # -------------------------------------------------
            # CANTIDAD DEL GRUPO
            # -------------------------------------------------

            if group_total != required:

                raise NotFoundException(
                    f"El grupo {index} de la promoción "
                    f"requiere {required} unidades y "
                    f"se seleccionaron {group_total}"
                )

        # -----------------------------------------------------
        # NO PUEDE HABER SELECCIONES SOBRANTES
        # -----------------------------------------------------

        if ungrouped:

            raise NotFoundException(
                "La promoción contiene más unidades "
                "de las permitidas"
            )

        # =====================================================
        # VALIDACIÓN DE STOCK
        # =====================================================

        old_map = {}

        if old_promotion_item:

            old_multiplier = int(
                old_promotion_item.get(
                    "quantity",
                    1
                )
            )

            for selection in old_promotion_item.get(
                "promotion_items",
                []
            ):

                pid = str(
                    selection["product_id"]
                )

                old_map[pid] = (
                    old_map.get(pid, 0)
                    + int(
                        selection["quantity"]
                    ) * old_multiplier
                )

        new_multiplier = int(quantity)

        new_map = {}

        for selection in normalized:

            pid = str(
                selection["product_id"]
            )

            # Una selección representa los productos
            # de UNA promoción.
            #
            # El multiplicador solamente se aplica si
            # realmente se venden varias promociones.

            required_stock = (
                int(selection["quantity"])
                * new_multiplier
            )

            new_map[pid] = (
                new_map.get(pid, 0)
                + required_stock
            )

        # -----------------------------------------------------
        # VALIDAR STOCK ADICIONAL
        # -----------------------------------------------------

        for pid, required_quantity in new_map.items():

            old_quantity = old_map.get(
                pid,
                0
            )

            additional = (
                required_quantity
                - old_quantity
            )

            if additional <= 0:
                continue

            product = await self.product_repository.get_by_id(
                pid
            )

            if not product:

                raise NotFoundException(
                    f"El producto con ID {pid} no existe"
                )

            if product["quantity"] < additional:

                raise NotFoundException(
                    f"No hay stock suficiente del producto: "
                    f"{product['name']}. "
                    f"Disponible: {product['quantity']}, "
                    f"solicitado adicionalmente: "
                    f"{additional}"
                )

        return normalized

    # =========================================================
    # PROCESAR PROMOCIÓN
    # =========================================================

    async def _process_promotion_item(
        self,
        item,
        old_item=None
    ):

        promotion_id = self._value(
            item,
            "promotion_id"
        )

        promotion = await self.promotion_repository.get_by_id(
            promotion_id
        )

        if not promotion:

            raise NotFoundException(
                f"La promoción con ID "
                f"{promotion_id} no existe"
            )

        if not promotion.get(
            "status",
            True
        ):

            raise NotFoundException(
                f"La promoción "
                f"'{promotion.get('name', '')}' "
                "está inactiva"
            )

        quantity = int(
            self._value(
                item,
                "quantity",
                1
            )
        )

        if quantity <= 0:

            raise NotFoundException(
                "La cantidad de la promoción "
                "debe ser mayor a 0"
            )

        selections = (
            self._normalize_promotion_selections(
                item
            )
        )

        old_promotion_item = (
            old_item
            if old_item
            and old_item.get("type") == "promotion"
            else None
        )

        normalized_selections = (
            await self._validate_promotion_selection(
                promotion,
                selections,
                quantity=quantity,
                old_promotion_item=old_promotion_item
            )
        )

        # -----------------------------------------------------
        # PRECIO DE LA PROMOCIÓN
        # -----------------------------------------------------

        unit_price = promotion.get(
            "price"
        )

        if unit_price is None:

            unit_price = promotion.get(
                "promotional_price"
            )

        if unit_price is None:

            raise NotFoundException(
                "La promoción no tiene "
                "un precio configurado"
            )

        subtotal = (
            float(unit_price)
            * quantity
        )

        return {
            "id": promotion_id,
            "type": "promotion",
            "promotion_id": promotion_id,
            "name": promotion.get(
                "name",
                "Promoción"
            ),
            "quantity": quantity,
            "unit_price": float(unit_price),
            "subtotal": subtotal,
            "status": True,
            "promotion_items": normalized_selections
        }, subtotal

    # =========================================================
    # PROCESAR ITEMS
    # =========================================================

    async def _process_items(
        self,
        items,
        old_items=None
    ):

        if not items:

            raise NotFoundException(
                "No se puede crear una comanda "
                "sin productos"
            )

        old_items = old_items or []

        old_normal = {}

        old_promotions = {}

        for old_item in old_items:

            if old_item.get(
                "type"
            ) == "promotion":

                old_promotions[
                    str(
                        old_item.get(
                            "promotion_id"
                        )
                    )
                ] = old_item

            else:

                pid = str(
                    old_item["product_id"]
                )

                old_normal[pid] = (
                    old_normal.get(
                        pid,
                        0
                    )
                    + old_item["quantity"]
                )

        order_items = []

        total_price = 0

        for item in items:

            # =================================================
            # PROMOCIÓN
            # =================================================

            if self._is_promotion_item(
                item
            ):

                promotion_item, subtotal = (
                    await self._process_promotion_item(
                        item,
                        old_promotions.get(
                            str(
                                self._value(
                                    item,
                                    "promotion_id"
                                )
                            )
                        )
                    )
                )

                order_items.append(
                    promotion_item
                )

                total_price += subtotal

                continue

            # =================================================
            # PRODUCTO NORMAL
            # =================================================

            product_id = self._value(
                item,
                "product_id"
            )

            quantity = int(
                self._value(
                    item,
                    "quantity",
                    0
                )
            )

            product = await self.product_repository.get_by_id(
                product_id
            )

            if not product:

                raise NotFoundException(
                    f"El producto con ID "
                    f"{product_id} no existe"
                )

            if not product["status"]:

                raise NotFoundException(
                    f"El producto "
                    f"'{product['name']}' "
                    "está inactivo."
                )

            if quantity <= 0:

                raise NotFoundException(
                    "La cantidad del producto "
                    "debe ser mayor a 0"
                )

            old_quantity = old_normal.get(
                str(product_id),
                0
            )

            additional_quantity = (
                quantity
                - old_quantity
            )

            if (
                additional_quantity > 0
                and product["quantity"]
                < additional_quantity
            ):

                raise NotFoundException(
                    f"No hay stock suficiente "
                    f"del producto: "
                    f"{product['name']}. "
                    f"Disponible: "
                    f"{product['quantity']}, "
                    f"solicitado adicionalmente: "
                    f"{additional_quantity}"
                )

            unit_price = product["price"]

            subtotal = (
                unit_price
                * quantity
            )

            order_items.append({
                "id": product_id,
                "type": "product",
                "product_id": product_id,
                "name": product["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "status": True
            })

            total_price += subtotal

        return (
            order_items,
            total_price
        )

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

        if data.status_payment == "cancelled":

            raise NotFoundException(
                "No se puede crear una orden "
                "directamente como cancelada"
            )

        # -----------------------------------------------------
        # PROCESAR ITEMS
        # -----------------------------------------------------

        items, total_price = (
            await self._process_items(
                data.items
            )
        )

        # -----------------------------------------------------
        # CAJA
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
        # FECHA
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
        # MOVIMIENTO DE CAJA
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

            # -------------------------------------------------
            # PROMOCIÓN
            # -------------------------------------------------

            if item.get(
                "type"
            ) == "promotion":

                promotion_quantity = int(
                    item.get(
                        "quantity",
                        1
                    )
                )

                for selection in item.get(
                    "promotion_items",
                    []
                ):

                    quantity = (
                        int(
                            selection["quantity"]
                        )
                        * promotion_quantity
                    )

                    movement = StockMovementCreate(

                        product_id=selection[
                            "product_id"
                        ],

                        type="outflow",

                        description=(
                            f"Venta pedido "
                            f"#{order['order_number']} "
                            f"- promoción "
                            f"{item['name']}"
                        ),

                        quantity=quantity,

                        order_id=order["id"],

                        status=True
                    )

                    await self.stock_movement_service.create(
                        movement
                    )

            # -------------------------------------------------
            # PRODUCTO NORMAL
            # -------------------------------------------------

            else:

                movement = StockMovementCreate(

                    product_id=item[
                        "product_id"
                    ],

                    type="outflow",

                    description=(
                        f"Venta pedido "
                        f"#{order['order_number']}"
                    ),

                    quantity=item[
                        "quantity"
                    ],

                    order_id=order["id"],

                    status=True
                )

                await self.stock_movement_service.create(
                    movement
                )

    # =========================================================
    # MOVIMIENTO DE CAJA
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
    # ACTUALIZAR MOVIMIENTO DE CAJA
    # =========================================================

    async def _update_sale_cash_movement(
        self,
        order_id,
        amount,
        method_payment,
        cash_register_id
    ):

        await self._get_cash_register(
            cash_register_id
        )

        movement = (
            await self.cash_movement_service
            .repository
            .collection
            .find_one({
                "order_id": str(order_id),
                "category": "sale",
                "status": True
            })
        )

        if not movement:

            raise NotFoundException(
                "No se encontró el movimiento "
                "de venta de la orden"
            )

        order = await self.repository.get_by_id(
            str(order_id)
        )

        if not order:

            raise NotFoundException(
                "No se encontró la orden"
            )

        return await self.cash_movement_service.repository.update(
            str(movement["_id"]),
            {
                "amount": amount,
                "method_payment": method_payment,
                "cash_register_id": str(
                    cash_register_id
                ),
                "description":
                    f"Venta pedido "
                    f"#{order['order_number']}"
            }
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
        # CANCELADA NO VUELVE ATRÁS
        # =====================================================

        if old_payment_status == "cancelled":

            if new_payment_status != "cancelled":

                raise NotFoundException(
                    "Una orden cancelada no puede "
                    "volver a cambiar su estado de pago"
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
        # NO EDITAR ITEMS SI PAGADA/CANCELADA
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
        # DATOS
        # -----------------------------------------------------

        update_data = data.model_dump(
            exclude_none=True,
            exclude_unset=True
        )

        # =====================================================
        # CAJA
        # =====================================================

        cash_register_id = (
            data.cash_register_id
            if data.cash_register_id is not None
            else old_order.get(
                "cash_register_id"
            )
        )

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
                    "Debe indicar la caja para "
                    "registrar el pago"
                )

            await self._get_cash_register(
                cash_register_id
            )

            method_payment = (
                data.method_payment
                if data.method_payment is not None
                else old_order["method_payment"]
            )

            await self._update_sale_cash_movement(
                order_id=str(
                    old_order["id"]
                ),
                amount=old_order[
                    "total_price"
                ],
                method_payment=method_payment,
                cash_register_id=cash_register_id
            )

            update_data[
                "cash_register_id"
            ] = cash_register_id

        # =====================================================
        # PENDING -> CANCELLED
        # =====================================================

        if (
            old_payment_status == "pending"
            and new_payment_status == "cancelled"
        ):

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
        # GUARDAR
        # =====================================================

        return await self.repository.update(
            order_id,
            update_data
        )

    # =========================================================
    # APLANAR STOCK
    # =========================================================

    def _flatten_stock_requirements(
        self,
        items
    ):

        result = {}

        for item in items or []:

            if item.get(
                "type"
            ) == "promotion":

                promotion_quantity = int(
                    item.get(
                        "quantity",
                        1
                    )
                )

                for selection in item.get(
                    "promotion_items",
                    []
                ):

                    pid = str(
                        selection[
                            "product_id"
                        ]
                    )

                    result[pid] = (
                        result.get(
                            pid,
                            0
                        )
                        + int(
                            selection[
                                "quantity"
                            ]
                        )
                        * promotion_quantity
                    )

            else:

                pid = str(
                    item["product_id"]
                )

                result[pid] = (
                    result.get(
                        pid,
                        0
                    )
                    + int(
                        item["quantity"]
                    )
                )

        return result

    # =========================================================
    # AJUSTAR STOCK AL EDITAR
    # =========================================================

    async def _adjust_order_stock(
        self,
        old_items,
        new_items,
        order_id
    ):

        old_map = self._flatten_stock_requirements(
            old_items
        )

        new_map = self._flatten_stock_requirements(
            new_items
        )

        product_ids = (
            set(old_map)
            .union(new_map)
        )

        for product_id in product_ids:

            difference = (
                new_map.get(
                    product_id,
                    0
                )
                - old_map.get(
                    product_id,
                    0
                )
            )

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

            elif difference < 0:

                movement = StockMovementCreate(

                    product_id=product_id,

                    type="inflow",

                    description=(
                        f"Quitado de pedido "
                        f"#{order_id}"
                    ),

                    quantity=abs(
                        difference
                    ),

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

        selected_cash_register_id = (
            cash_register_id
            or order.get(
                "cash_register_id"
            )
        )

        if not selected_cash_register_id:

            raise NotFoundException(
                "Debe indicar una caja para "
                "realizar el reembolso"
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

            method_payment=order[
                "method_payment"
            ],

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

            # -------------------------------------------------
            # PROMOCIÓN
            # -------------------------------------------------

            if item.get(
                "type"
            ) == "promotion":

                promotion_quantity = int(
                    item.get(
                        "quantity",
                        1
                    )
                )

                for selection in item.get(
                    "promotion_items",
                    []
                ):

                    quantity = (
                        int(
                            selection[
                                "quantity"
                            ]
                        )
                        * promotion_quantity
                    )

                    movement = StockMovementCreate(

                        product_id=selection[
                            "product_id"
                        ],

                        type="inflow",

                        description=(
                            f"Devolución pedido "
                            f"#{order['order_number']} "
                            f"- promoción "
                            f"{item['name']}"
                        ),

                        quantity=quantity,

                        order_id=order["id"],

                        status=True
                    )

                    await self.stock_movement_service.create(
                        movement
                    )

            # -------------------------------------------------
            # PRODUCTO NORMAL
            # -------------------------------------------------

            else:

                movement = StockMovementCreate(

                    product_id=item[
                        "product_id"
                    ],

                    type="inflow",

                    description=(
                        f"Devolución pedido "
                        f"#{order['order_number']}"
                    ),

                    quantity=item[
                        "quantity"
                    ],

                    order_id=order["id"],

                    status=True
                )

                await self.stock_movement_service.create(
                    movement
                )