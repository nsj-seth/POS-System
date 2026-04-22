from models.customer import Customer
from database.connection import get_connection


class CustomerService:

    # ── Read ──────────────────────────────────────────────────────────────────
    def get_all(self, search: str = "") -> list[Customer]:
        conn = get_connection()
        if search:
            rows = conn.execute("""
                SELECT  c.*,
                        COUNT(s.id)             AS total_purchases,
                        COALESCE(SUM(s.total_amount), 0) AS total_spent
                FROM    customers c
                LEFT JOIN sales s ON s.customer_id = c.id
                WHERE   c.name  LIKE ?
                   OR   c.phone LIKE ?
                   OR   c.email LIKE ?
                GROUP BY c.id
                ORDER BY c.name
            """, (f"%{search}%",) * 3).fetchall()
        else:
            rows = conn.execute("""
                SELECT  c.*,
                        COUNT(s.id)             AS total_purchases,
                        COALESCE(SUM(s.total_amount), 0) AS total_spent
                FROM    customers c
                LEFT JOIN sales s ON s.customer_id = c.id
                GROUP BY c.id
                ORDER BY c.name
            """).fetchall()
        conn.close()
        return [self._row_to_customer(r) for r in rows]

    def get_by_id(self, customer_id: int) -> Customer | None:
        conn = get_connection()
        row = conn.execute("""
            SELECT  c.*,
                    COUNT(s.id)             AS total_purchases,
                    COALESCE(SUM(s.total_amount), 0) AS total_spent
            FROM    customers c
            LEFT JOIN sales s ON s.customer_id = c.id
            WHERE   c.id = ?
            GROUP BY c.id
        """, (customer_id,)).fetchone()
        conn.close()
        return self._row_to_customer(row) if row else None

    def get_purchase_history(self, customer_id: int) -> list[dict]:
        conn = get_connection()
        rows = conn.execute("""
            SELECT  s.id,
                    s.total_amount,
                    s.payment_method,
                    s.created_at,
                    u.username AS cashier
            FROM    sales s
            LEFT JOIN users u ON u.id = s.cashier_id
            WHERE   s.customer_id = ?
            ORDER BY s.created_at DESC
            LIMIT 50
        """, (customer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Write ─────────────────────────────────────────────────────────────────
    def create(self, name: str, phone: str | None,
               email: str | None) -> tuple[bool, str]:
        if not name.strip():
            return False, "Customer name is required."
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)",
                (name.strip(), phone or None, email or None),
            )
            conn.commit()
            conn.close()
            return True, "Customer added successfully."
        except Exception as e:
            return False, str(e)

    def update(self, customer_id: int, name: str,
               phone: str | None, email: str | None) -> tuple[bool, str]:
        if not name.strip():
            return False, "Customer name is required."
        try:
            conn = get_connection()
            conn.execute(
                """UPDATE customers
                   SET name=?, phone=?, email=?
                   WHERE id=?""",
                (name.strip(), phone or None, email or None, customer_id),
            )
            conn.commit()
            conn.close()
            return True, "Customer updated successfully."
        except Exception as e:
            return False, str(e)

    def delete(self, customer_id: int) -> tuple[bool, str]:
        try:
            conn = get_connection()
            conn.execute(
                "DELETE FROM customers WHERE id = ?", (customer_id,)
            )
            conn.commit()
            conn.close()
            return True, "Customer deleted."
        except Exception as e:
            return False, str(e)

    # ── Helper ────────────────────────────────────────────────────────────────
    def _row_to_customer(self, row) -> Customer:
        return Customer(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            email=row["email"],
            total_purchases=row["total_purchases"],
            total_spent=row["total_spent"],
            created_at=row["created_at"],
        )