from database.connection import get_connection


class DashboardService:
    """Queries for dashboard summary statistics."""

    def get_stats(self) -> dict:
        conn = get_connection()

        # Sales made today
        today_sales = conn.execute("""
            SELECT COUNT(*)        AS count,
                   COALESCE(SUM(total_amount), 0) AS revenue
            FROM   sales
            WHERE  DATE(created_at) = DATE('now')
        """).fetchone()

        # Total products in the system
        total_products = conn.execute(
            "SELECT COUNT(*) AS count FROM products"
        ).fetchone()

        # Low stock items (quantity <= low_stock_qty)
        low_stock = conn.execute("""
            SELECT COUNT(*) AS count
            FROM   products
            WHERE  quantity <= low_stock_qty
        """).fetchone()

        # Total customers
        total_customers = conn.execute(
            "SELECT COUNT(*) AS count FROM customers"
        ).fetchone()

        # 8 most recent sales
        recent_sales = conn.execute("""
            SELECT  s.id,
                    COALESCE(c.name, 'Walk-in') AS customer,
                    u.username                  AS cashier,
                    s.total_amount,
                    s.payment_method,
                    s.created_at
            FROM    sales s
            LEFT JOIN customers c ON c.id = s.customer_id
            LEFT JOIN users     u ON u.id = s.cashier_id
            ORDER BY s.created_at DESC
            LIMIT 8
        """).fetchall()

        conn.close()

        return {
            "today_count":      today_sales["count"],
            "today_revenue":    today_sales["revenue"],
            "total_products":   total_products["count"],
            "low_stock_count":  low_stock["count"],
            "total_customers":  total_customers["count"],
            "recent_sales":     [dict(r) for r in recent_sales],
        }