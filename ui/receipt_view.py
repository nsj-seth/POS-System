import customtkinter as ctk
from services.receipt_service import ReceiptService


class ReceiptView(ctk.CTkFrame):
    """Receipt screen shown after a successful payment."""

    def __init__(self, parent, current_user, sale_id: int,
                 on_new_sale=None, on_dashboard=None):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._user        = current_user
        self._sale_id     = sale_id
        self._svc         = ReceiptService()
        self._on_new_sale  = on_new_sale
        self._on_dashboard = on_dashboard

        self._receipt_data = self._svc.get_receipt_data(sale_id)
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        if not self._receipt_data:
            ctk.CTkLabel(
                self, text="Receipt not found.",
                font=ctk.CTkFont(size=16)
            ).place(relx=0.5, rely=0.5, anchor="center")
            return

        sale  = self._receipt_data["sale"]
        items = self._receipt_data["items"]

        # ── Page header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(
            header,
            text="✅  Payment Successful",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#1e8449", "#2ecc71"),
        ).pack(side="left")

        # Action buttons top-right
        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🖨  Print Receipt",
            width=140,
            height=36,
            corner_radius=8,
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            text_color=("gray10", "gray90"),
            command=self._print_receipt,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="＋  New Sale",
            width=120,
            height=36,
            corner_radius=8,
            command=self._new_sale,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="🏠  Dashboard",
            width=120,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            command=self._go_dashboard,
        ).pack(side="left")

        # ── Two column layout ─────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_receipt_panel(body, sale, items)
        self._build_summary_panel(body, sale)

    # ── Left: visual receipt ──────────────────────────────────────────────────
    def _build_receipt_panel(self, parent, sale, items):
        outer = ctk.CTkFrame(parent, corner_radius=12)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent", corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Receipt card
        card = ctk.CTkFrame(
            scroll,
            fg_color=("white", "gray15"),
            corner_radius=12,
        )
        card.pack(fill="x", padx=12, pady=12)

        def centre_label(text, size=12, bold=False, color=None):
            kwargs = dict(
                text=text,
                font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"),
                anchor="center",
            )
            if color:
                kwargs["text_color"] = color
            ctk.CTkLabel(card, **kwargs).pack(fill="x", padx=20)

        def divider():
            ctk.CTkFrame(
                card, height=1,
                fg_color=("gray80", "gray35"),
            ).pack(fill="x", padx=16, pady=6)

        def info_row(left, right, bold=False):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=1)
            ctk.CTkLabel(
                row, text=left,
                font=ctk.CTkFont(size=12,
                                 weight="bold" if bold else "normal"),
                anchor="w",
                text_color=("gray40", "gray60"),
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=right,
                font=ctk.CTkFont(size=12,
                                 weight="bold" if bold else "normal"),
                anchor="e",
            ).pack(side="right")

        # ── Store header ──────────────────────────────────────────────────────
        ctk.CTkLabel(card, text="").pack(pady=4)
        centre_label("⚡ SwiftPOS Store", size=16, bold=True)
        centre_label("Kumasi, Ashanti Region, Ghana",
                     color=("gray50", "gray50"))
        centre_label("+233 00 000 0000", color=("gray50", "gray50"))

        divider()

        centre_label(f"RECEIPT  #{self._sale_id:05d}", size=13, bold=True)

        try:
            from datetime import datetime
            dt = datetime.fromisoformat(sale["created_at"])
            date_str = dt.strftime("%d %b %Y  •  %H:%M")
        except Exception:
            date_str = sale["created_at"][:16]

        centre_label(date_str, color=("gray50", "gray50"))
        ctk.CTkLabel(card, text="").pack(pady=2)

        info_row("Cashier",   sale["cashier_name"])
        info_row("Customer",  sale["customer_name"])

        divider()

        # ── Items ─────────────────────────────────────────────────────────────
        for item in items:
            name = item["product_name"] or "Unknown Product"
            row  = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)

            left_col = ctk.CTkFrame(row, fg_color="transparent")
            left_col.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                left_col, text=name,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                left_col,
                text=f"{item['quantity']} × GH₵ {item['unit_price']:,.2f}",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray50"),
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                row,
                text=f"GH₵ {item['subtotal']:,.2f}",
                font=ctk.CTkFont(size=12),
                anchor="e",
            ).pack(side="right", padx=(8, 0))

        divider()

        # ── Totals ────────────────────────────────────────────────────────────
        raw_sub = sale["total_amount"] + sale["discount_amount"]
        info_row("Subtotal",  f"GH₵ {raw_sub:,.2f}")
        info_row("Discount",  f"− GH₵ {sale['discount_amount']:,.2f}")

        # Bold total row
        total_row = ctk.CTkFrame(card, fg_color="transparent")
        total_row.pack(fill="x", padx=20, pady=(4, 2))
        ctk.CTkLabel(
            total_row, text="TOTAL",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            total_row,
            text=f"GH₵ {sale['total_amount']:,.2f}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e",
        ).pack(side="right")

        divider()

        # ── Payment info ──────────────────────────────────────────────────────
        method = sale["payment_method"].replace("_", " ").title()
        info_row("Payment Method", method)
        info_row("Amount Paid",
                 f"GH₵ {sale['amount_paid']:,.2f}")
        info_row("Change Given",
                 f"GH₵ {sale['change_given']:,.2f}")

        divider()

        centre_label("Thank you for your purchase! 🙏",
                     size=12, color=("gray50", "gray50"))
        centre_label("Powered by SwiftPOS",
                     size=11, color=("gray60", "gray60"))
        ctk.CTkLabel(card, text="").pack(pady=4)

    # ── Right: summary panel ──────────────────────────────────────────────────
    def _build_summary_panel(self, parent, sale):
        panel = ctk.CTkFrame(parent, corner_radius=12)
        panel.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            panel,
            text="Sale Summary",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 12))

        def stat_card(icon, label, value, color=None):
            card = ctk.CTkFrame(
                panel,
                fg_color=("gray88", "gray22"),
                corner_radius=10,
            )
            card.pack(fill="x", padx=12, pady=5)

            ctk.CTkLabel(
                card,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(size=11),
                text_color="gray50",
                anchor="w",
            ).pack(fill="x", padx=14, pady=(12, 2))

            lbl = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold"),
                anchor="w",
            )
            if color:
                lbl.configure(text_color=color)
            lbl.pack(fill="x", padx=14, pady=(0, 12))

        stat_card("🧾", "Sale ID",
                  f"#{self._sale_id:05d}")
        stat_card("💰", "Total Charged",
                  f"GH₵ {sale['total_amount']:,.2f}",
                  color=("#1e8449", "#2ecc71"))
        stat_card("💵", "Amount Paid",
                  f"GH₵ {sale['amount_paid']:,.2f}")
        stat_card("🔄", "Change Given",
                  f"GH₵ {sale['change_given']:,.2f}")
        stat_card("💳", "Method",
                  sale["payment_method"].replace("_", " ").title())
        stat_card("👤", "Customer",
                  sale["customer_name"])
        stat_card("🧑‍💼", "Cashier",
                  sale["cashier_name"])

        # Print status label
        self._print_status = ctk.CTkLabel(
            panel, text="",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            wraplength=200,
        )
        self._print_status.pack(padx=14, pady=(8, 0))

    # ══════════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════════════════
    def _print_receipt(self):
        self._print_status.configure(
            text="Sending to printer…", text_color="gray50"
        )
        self.after(100, self._do_print)

    def _do_print(self):
        ok, msg = self._svc.print_receipt(self._sale_id)
        if ok:
            self._print_status.configure(
                text="✅ " + msg, text_color=("#1e8449", "#2ecc71")
            )
        else:
            self._print_status.configure(
                text="⚠️ " + msg, text_color=("#c0392b", "#e05252")
            )

    def _new_sale(self):
        if self._on_new_sale:
            self._on_new_sale()

    def _go_dashboard(self):
        if self._on_dashboard:
            self._on_dashboard()