from dataclasses import dataclass, field
from models.product import Product


@dataclass
class CartItem:
    product:   Product
    quantity:  int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)


class Cart:
    """Holds cart items and discount for one sale transaction."""

    def __init__(self):
        self._items: list[CartItem] = []
        self.discount: float = 0.0

    # ── Mutations ─────────────────────────────────────────────────────────────
    def add_item(self, product: Product, quantity: int = 1) -> None:
        for item in self._items:
            if item.product.id == product.id:
                new_qty = item.quantity + quantity
                if new_qty > product.quantity:
                    raise ValueError(
                        f"Only {product.quantity} units of "
                        f"'{product.name}' in stock."
                    )
                item.quantity = new_qty
                return

        if quantity > product.quantity:
            raise ValueError(
                f"Only {product.quantity} units of '{product.name}' in stock."
            )
        self._items.append(
            CartItem(product=product, quantity=quantity,
                     unit_price=product.price)
        )

    def remove_item(self, product_id: int) -> None:
        self._items = [i for i in self._items if i.product.id != product_id]

    def update_quantity(self, product_id: int, quantity: int) -> None:
        for item in self._items:
            if item.product.id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                    return
                if quantity > item.product.quantity:
                    raise ValueError(
                        f"Only {item.product.quantity} units of "
                        f"'{item.product.name}' in stock."
                    )
                item.quantity = quantity
                return

    def clear(self) -> None:
        self._items.clear()
        self.discount = 0.0

    # ── Computed ──────────────────────────────────────────────────────────────
    @property
    def items(self) -> list[CartItem]:
        return list(self._items)

    @property
    def subtotal(self) -> float:
        return round(sum(i.subtotal for i in self._items), 2)

    @property
    def discount_amount(self) -> float:
        return round(min(self.discount, self.subtotal), 2)

    @property
    def total(self) -> float:
        return round(self.subtotal - self.discount_amount, 2)

    @property
    def item_count(self) -> int:
        return sum(i.quantity for i in self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0