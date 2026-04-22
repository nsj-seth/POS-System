from database.connection import get_connection
from datetime import datetime, timedelta


class ReportService:

    # ── Daily sales report ────────────────────────────────────────────────────
    def get_daily_summary(self, date_str: str) -> dict:
        """
        Returns sales summary for a given date (YYYY-MM-DD).
        """
        conn = get_connection()

        summary = conn.execute("""
            SELECT  COUNT(*)                        AS total_transactions,
                    COALESCE(SUM(total_amount), 0)  AS total_revenue,
                    COALESCE(SUM(discount_amount),0) AS total_discounts,
                    COALESCE(AVG(total_amount), 0)  AS avg_sale_value,
                    SUM(CASE WHEN payment_method='cash'
                             THEN 1 ELSE 0 END)     AS cash_count,
                    SUM(CASE WHEN payment_method='mobile_money'
                             THEN 1 ELSE 0 END)     AS momo_count,
                    COALESCE(SUM(CASE WHEN payment_method='cash'
                             THEN total_amount ELSE 0 END), 0) AS cash_revenue,
                    COALESCE(SUM(CASE WHEN payment_method='mobile_money'
                             THEN total_amount ELSE 0 END), 0) AS momo_revenue
            FROM    sales
            WHERE   DATE(created_at) = ?
        """, (date_str,)).fetchone()

        transactions = conn.execute("""
            SELECT  s.id,
                    COALESCE(c.name,'Walk-in')  AS customer,
                    u.username                  AS cashier,
                    s.total_amount,
                    s.discount_amount,
                    s.payment_method,
                    s.created_at,
                    COUNT(si.id)                AS item_count
            FROM    sales s
            LEFT JOIN customers  c  ON c.id  = s.customer_id
            LEFT JOIN users      u  ON u.id  = s.cashier_id
            LEFT JOIN sale_items si ON si.sale_id = s.id
            WHERE   DATE(s.created_at) = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """, (date_str,)).fetchall()

        # Top 5 products sold on that day
        top_products = conn.execute("""
            SELECT  p.name,
                    SUM(si.quantity)    AS units_sold,
                    SUM(si.subtotal)    AS revenue
            FROM    sale_items si
            JOIN    sales    s  ON s.id  = si.sale_id
            LEFT JOIN products p ON p.id = si.product_id
            WHERE   DATE(s.created_at) = ?
            GROUP BY si.product_id
            ORDER BY units_sold DESC
            LIMIT 5
        """, (date_str,)).fetchall()

        conn.close()

        return {
            "date":            date_str,
            "summary":         dict(summary),
            "transactions":    [dict(r) for r in transactions],
            "top_products":    [dict(r) for r in top_products],
        }

    def get_date_range_revenue(self, days: int = 7) -> list[dict]:
        """Revenue per day for the last N days (for a mini chart)."""
        conn = get_connection()
        rows = conn.execute("""
            SELECT  DATE(created_at)               AS day,
                    COUNT(*)                        AS transactions,
                    COALESCE(SUM(total_amount), 0)  AS revenue
            FROM    sales
            WHERE   DATE(created_at) >= DATE('now', ?)
            GROUP BY day
            ORDER BY day ASC
        """, (f"-{days} days",)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Inventory report ──────────────────────────────────────────────────────
    def get_inventory_report(self, search: str = "") -> dict:
        conn = get_connection()

        if search:
            products = conn.execute("""
                SELECT  p.*,
                        c.name  AS category_name,
                        COALESCE(SUM(si.quantity), 0) AS total_sold
                FROM    products p
                LEFT JOIN categories  c  ON c.id  = p.category_id
                LEFT JOIN sale_items  si ON si.product_id = p.id
                WHERE   p.name LIKE ? OR p.barcode LIKE ?
                GROUP BY p.id
                ORDER BY p.name
            """, (f"%{search}%", f"%{search}%")).fetchall()
        else:
            products = conn.execute("""
                SELECT  p.*,
                        c.name  AS category_name,
                        COALESCE(SUM(si.quantity), 0) AS total_sold
                FROM    products p
                LEFT JOIN categories  c  ON c.id  = p.category_id
                LEFT JOIN sale_items  si ON si.product_id = p.id
                GROUP BY p.id
                ORDER BY p.name
            """).fetchall()

        stats = conn.execute("""
            SELECT  COUNT(*)                                AS total_products,
                    SUM(quantity)                           AS total_units,
                    SUM(quantity * price)                   AS stock_value,
                    SUM(CASE WHEN quantity <= low_stock_qty
                             THEN 1 ELSE 0 END)             AS low_stock_count,
                    SUM(CASE WHEN quantity = 0
                             THEN 1 ELSE 0 END)             AS out_of_stock
            FROM products
        """).fetchone()

        conn.close()
        return {
            "products": [dict(r) for r in products],
            "stats":    dict(stats),
        }

    def export_inventory_csv(self, filepath: str) -> tuple[bool, str]:
        """Write inventory report to a CSV file."""
        try:
            import csv
            data = self.get_inventory_report()

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "Name", "Category", "Price (GH₵)",
                    "Quantity", "Low Stock Qty", "Stock Value (GH₵)",
                    "Total Sold", "Barcode"
                ])
                for p in data["products"]:
                    writer.writerow([
                        p["id"],
                        p["name"],
                        p["category_name"] or "",
                        f"{p['price']:.2f}",
                        p["quantity"],
                        p["low_stock_qty"],
                        f"{p['price'] * p['quantity']:.2f}",
                        p["total_sold"],
                        p["barcode"] or "",
                    ])
            return True, f"Exported to {filepath}"
        except Exception as e:
            return False, str(e)

    def export_daily_csv(self, date_str: str,
                         filepath: str) -> tuple[bool, str]:
        """Write daily sales report to a CSV file."""
        try:
            import csv
            data = self.get_daily_summary(date_str)

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Sale ID", "Customer", "Cashier",
                    "Total (GH₵)", "Discount (GH₵)",
                    "Payment Method", "Items", "Time"
                ])
                for t in data["transactions"]:
                    writer.writerow([
                        t["id"],
                        t["customer"],
                        t["cashier"] or "",
                        f"{t['total_amount']:.2f}",
                        f"{t['discount_amount']:.2f}",
                        t["payment_method"].replace("_", " ").title(),
                        t["item_count"],
                        t["created_at"][:16],
                    ])
            return True, f"Exported to {filepath}"
        except Exception as e:
            return False, str(e)