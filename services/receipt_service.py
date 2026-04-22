from services.sales_service import SalesService
from datetime import datetime


class ReceiptService:
    """Formats sale data into printable receipt text."""

    STORE_NAME    = "SwiftPOS Store"
    STORE_ADDRESS = "Kumasi, Ashanti Region, Ghana"
    STORE_PHONE   = "+233 00 000 0000"
    RECEIPT_WIDTH = 42   # characters wide

    def __init__(self):
        self._sales_svc = SalesService()

    def get_receipt_data(self, sale_id: int) -> dict | None:
        """Return structured receipt data for a given sale."""
        return self._sales_svc.get_sale_details(sale_id)

    def format_receipt_text(self, sale_id: int) -> str | None:
        """
        Build a plain-text receipt string suitable for printing
        or saving to file.
        """
        data = self.get_receipt_data(sale_id)
        if not data:
            return None

        sale  = data["sale"]
        items = data["items"]
        w     = self.RECEIPT_WIDTH
        line  = "─" * w

        def centre(text: str) -> str:
            return text.center(w)

        def row(left: str, right: str) -> str:
            space = w - len(left) - len(right)
            return left + " " * max(space, 1) + right

        # Parse date
        try:
            dt  = datetime.fromisoformat(sale["created_at"])
            date_str = dt.strftime("%d %b %Y  %H:%M")
        except Exception:
            date_str = sale["created_at"][:16]

        lines = [
            centre(self.STORE_NAME),
            centre(self.STORE_ADDRESS),
            centre(self.STORE_PHONE),
            line,
            centre(f"RECEIPT  #  {sale_id:05d}"),
            row("Date:", date_str),
            row("Cashier:", sale["cashier_name"]),
            row("Customer:", sale["customer_name"]),
            line,
        ]

        # Items
        for item in items:
            name     = item["product_name"] or "Unknown"
            qty      = item["quantity"]
            price    = item["unit_price"]
            subtotal = item["subtotal"]

            # Truncate long names
            if len(name) > 22:
                name = name[:19] + "…"

            lines.append(row(f"  {name}", f"GH₵ {subtotal:,.2f}"))
            lines.append(f"    {qty} x GH₵ {price:,.2f}")

        lines += [
            line,
            row("Subtotal:",
                f"GH₵ {sale['total_amount'] + sale['discount_amount']:,.2f}"),
            row("Discount:",
                f"- GH₵ {sale['discount_amount']:,.2f}"),
            row("TOTAL:",
                f"GH₵ {sale['total_amount']:,.2f}"),
            line,
            row("Payment:",
                sale["payment_method"].replace("_", " ").title()),
            row("Amount Paid:",
                f"GH₵ {sale['amount_paid']:,.2f}"),
            row("Change:",
                f"GH₵ {sale['change_given']:,.2f}"),
            line,
            centre("Thank you for your purchase!"),
            centre("Powered by SwiftPOS"),
            "",
        ]

        return "\n".join(lines)

    def print_receipt(self, sale_id: int) -> tuple[bool, str]:
        """
        Send receipt to the default system printer.
        Falls back gracefully if printing is unavailable.
        """
        text = self.format_receipt_text(sale_id)
        if not text:
            return False, "Sale not found."

        try:
            import tempfile, os, subprocess, sys

            # Write to a temp text file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt",
                delete=False, encoding="utf-8"
            ) as f:
                f.write(text)
                tmp_path = f.name

            if sys.platform == "win32":
                os.startfile(tmp_path, "print")
            elif sys.platform == "darwin":
                subprocess.run(["lpr", tmp_path], check=True)
            else:
                subprocess.run(["lpr", tmp_path], check=True)

            return True, "Receipt sent to printer."

        except Exception as e:
            return False, f"Print failed: {e}"