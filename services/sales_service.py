from models.cart import Cart
from database.connection import get_connection


class SalesService:
    """Handles saving a completed sale and updating inventory."""

    def process_sale(
        self,
        cart:           Cart,
        payment_method: str,
        amount_paid:    float,
        cashier_id:     int,
        customer_id:    int | None = None,
    ) -> tuple[bool, str, int | None]:
        """
        Persist the sale, deduct stock.
        Returns (success, message, sale_id).
        """
        if cart.is_empty():
            return False, "Cart is empty.", None

        if amount_paid < cart.total:
            return False, "Amount paid is less than total.", None

        conn = get_connection()
        try:
            change = round(amount_paid - cart.total, 2)

            # ── Insert sale header ─────────────────────────────────────────
            cursor = conn.execute("""
                INSERT INTO sales
                    (customer_id, cashier_id, total_amount,
                     discount_amount, payment_method,
                     amount_paid, change_given)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                cashier_id,
                cart.total,
                cart.discount_amount,
                payment_method,
                amount_paid,
                change,
            ))
            sale_id = cursor.lastrowid

            # ── Insert line items + deduct stock ──────────────────────────
            for item in cart.items:
                conn.execute("""
                    INSERT INTO sale_items
                        (sale_id, product_id, quantity, unit_price, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    sale_id,
                    item.product.id,
                    item.quantity,
                    item.unit_price,
                    item.subtotal,
                ))

                conn.execute("""
                    UPDATE products
                    SET    quantity = quantity - ?
                    WHERE  id = ?
                """, (item.quantity, item.product.id))

            conn.commit()
            return True, "Sale completed successfully.", sale_id

        except Exception as e:
            conn.rollback()
            return False, str(e), None
        finally:
            conn.close()

    def get_sale_details(self, sale_id: int) -> dict | None:
        """Fetch a completed sale with all its line items."""
        conn = get_connection()

        sale = conn.execute("""
            SELECT  s.*,
                    COALESCE(c.name, 'Walk-in Customer') AS customer_name,
                    u.username AS cashier_name
            FROM    sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            LEFT JOIN users     u ON u.id = s.cashier_id
            WHERE   s.id = ?
        """, (sale_id,)).fetchone()

        if not sale:
            conn.close()
            return None

        items = conn.execute("""
            SELECT  si.*,
                    p.name AS product_name
            FROM    sale_items si
            LEFT JOIN products p ON p.id = si.product_id
            WHERE   si.sale_id = ?
        """, (sale_id,)).fetchall()

        conn.close()

        return {
            "sale":  dict(sale),
            "items": [dict(i) for i in items],
        }