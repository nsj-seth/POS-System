from models.product import Product
from database.connection import get_connection


class ProductService:

    # ── Read ──────────────────────────────────────────────────────────────────
    def get_all(self, search: str = "") -> list[Product]:
        conn = get_connection()
        if search:
            rows = conn.execute("""
                SELECT p.*, c.name AS category_name
                FROM   products p
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE  p.name LIKE ? OR p.barcode LIKE ?
                ORDER BY p.name
            """, (f"%{search}%", f"%{search}%")).fetchall()
        else:
            rows = conn.execute("""
                SELECT p.*, c.name AS category_name
                FROM   products p
                LEFT JOIN categories c ON c.id = p.category_id
                ORDER BY p.name
            """).fetchall()
        conn.close()
        return [self._row_to_product(r) for r in rows]

    def get_by_id(self, product_id: int) -> Product | None:
        conn = get_connection()
        row = conn.execute("""
            SELECT p.*, c.name AS category_name
            FROM   products p
            LEFT JOIN categories c ON c.id = p.category_id
            WHERE  p.id = ?
        """, (product_id,)).fetchone()
        conn.close()
        return self._row_to_product(row) if row else None

    def get_categories(self) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, name FROM categories ORDER BY name"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Write ─────────────────────────────────────────────────────────────────
    def create(self, name: str, category_id: int | None, price: float,
               quantity: int, barcode: str | None,
               low_stock_qty: int) -> tuple[bool, str]:
        try:
            conn = get_connection()
            conn.execute("""
                INSERT INTO products
                    (name, category_id, price, quantity, barcode, low_stock_qty)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name.strip(), category_id, price, quantity,
                  barcode or None, low_stock_qty))
            conn.commit()
            conn.close()
            return True, "Product created successfully."
        except Exception as e:
            return False, str(e)

    def update(self, product_id: int, name: str, category_id: int | None,
               price: float, quantity: int, barcode: str | None,
               low_stock_qty: int) -> tuple[bool, str]:
        try:
            conn = get_connection()
            conn.execute("""
                UPDATE products
                SET    name=?, category_id=?, price=?, quantity=?,
                       barcode=?, low_stock_qty=?
                WHERE  id=?
            """, (name.strip(), category_id, price, quantity,
                  barcode or None, low_stock_qty, product_id))
            conn.commit()
            conn.close()
            return True, "Product updated successfully."
        except Exception as e:
            return False, str(e)

    def delete(self, product_id: int) -> tuple[bool, str]:
        try:
            conn = get_connection()
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            return True, "Product deleted."
        except Exception as e:
            return False, str(e)

    # ── Helper ────────────────────────────────────────────────────────────────
    def _row_to_product(self, row) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            category_id=row["category_id"],
            category_name=row["category_name"],
            price=row["price"],
            quantity=row["quantity"],
            barcode=row["barcode"],
            low_stock_qty=row["low_stock_qty"],
        )