import customtkinter as ctk
from services.dashboard_service import DashboardService


class DashboardView(ctk.CTkFrame):
    """Main dashboard with stat cards and recent sales table."""

    REFRESH_MS = 30_000   # auto-refresh every 30 seconds

    def __init__(self, parent, current_user):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._svc  = DashboardService()
        self._user = current_user
        self._after_id = None

        self._build_ui()
        self._load_data()

    # ── UI skeleton ───────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header row ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        self._refresh_btn = ctk.CTkButton(
            header,
            text="↻  Refresh",
            width=100,
            height=32,
            corner_radius=8,
            command=self._load_data,
        )
        self._refresh_btn.pack(side="right")

        self._last_updated = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=11), text_color="gray50"
        )
        self._last_updated.pack(side="right", padx=(0, 12))

        # ── Stat cards row ────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=24, pady=20)

        # We'll keep references so _load_data can update values
        self._cards = {}
        card_defs = [
            ("today_count",     "Today's Sales",    "🛍️",  None),
            ("today_revenue",   "Today's Revenue",  "💰",  None),
            ("total_products",  "Total Products",   "📦",  None),
            ("low_stock_count", "Low Stock Alerts", "⚠️",  "#c0392b"),
            ("total_customers", "Customers",        "👥",  None),
        ]

        for i, (key, title, icon, accent) in enumerate(card_defs):
            card = self._make_stat_card(cards_frame, title, icon, accent)
            card.grid(row=0, column=i, padx=6, sticky="ew")
            cards_frame.grid_columnconfigure(i, weight=1)
            self._cards[key] = card

        # ── Recent sales table ────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Recent Sales",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 8))

        table_frame = ctk.CTkFrame(self, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Table headers
        headers = ["ID", "Customer", "Cashier", "Amount (GH₵)", "Method", "Time"]
        widths  = [50, 180, 120, 130, 120, 160]

        header_row = ctk.CTkFrame(table_frame, fg_color=("gray80", "gray25"),
                                  corner_radius=8)
        header_row.pack(fill="x", padx=8, pady=(8, 0))

        for col, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(
                header_row,
                text=h,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=w,
                anchor="w",
            ).grid(row=0, column=col, padx=(10 if col == 0 else 4), pady=8,
                   sticky="w")

        # Scrollable rows area
        self._rows_frame = ctk.CTkScrollableFrame(
            table_frame, fg_color="transparent", corner_radius=0
        )
        self._rows_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self._col_widths = widths

    # ── Stat card widget factory ──────────────────────────────────────────────
    def _make_stat_card(self, parent, title, icon, accent_color):
        card = ctk.CTkFrame(parent, corner_radius=12, height=110)
        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text=f"{icon}  {title}",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 2))

        value_color = accent_color if accent_color else ("gray10", "gray90")
        value_lbl = ctk.CTkLabel(
            card,
            text="—",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=value_color,
            anchor="w",
        )
        value_lbl.pack(fill="x", padx=16)

        # Store the value label inside the card frame for later updates
        card._value_label = value_lbl
        return card

    # ── Data loading ──────────────────────────────────────────────────────────
    def _load_data(self):
        try:
            stats = self._svc.get_stats()
            self._update_cards(stats)
            self._update_table(stats["recent_sales"])
            self._update_timestamp()
        except Exception as e:
            print(f"[Dashboard] Error loading data: {e}")

        # Schedule next refresh (cancel previous if any)
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(self.REFRESH_MS, self._load_data)

    def _update_cards(self, stats: dict):
        self._cards["today_count"]._value_label.configure(
            text=str(stats["today_count"])
        )
        self._cards["today_revenue"]._value_label.configure(
            text=f"GH₵ {stats['today_revenue']:,.2f}"
        )
        self._cards["total_products"]._value_label.configure(
            text=str(stats["total_products"])
        )
        self._cards["low_stock_count"]._value_label.configure(
            text=str(stats["low_stock_count"])
        )
        self._cards["total_customers"]._value_label.configure(
            text=str(stats["total_customers"])
        )

    def _update_table(self, rows: list):
        # Clear old rows
        for w in self._rows_frame.winfo_children():
            w.destroy()

        if not rows:
            ctk.CTkLabel(
                self._rows_frame,
                text="No sales recorded yet.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, row in enumerate(rows):
            bg = ("gray92", "gray17") if i % 2 == 0 else ("gray86", "gray20")
            row_frame = ctk.CTkFrame(
                self._rows_frame, fg_color=bg, corner_radius=6, height=36
            )
            row_frame.pack(fill="x", pady=1)
            row_frame.pack_propagate(False)

            # Format time to be readable
            time_str = row["created_at"][:16].replace("T", "  ")

            values = [
                f"#{row['id']}",
                row["customer"],
                row["cashier"] or "—",
                f"GH₵ {row['total_amount']:,.2f}",
                row["payment_method"].replace("_", " ").title(),
                time_str,
            ]

            for col, (val, w) in enumerate(zip(values, self._col_widths)):
                ctk.CTkLabel(
                    row_frame,
                    text=val,
                    font=ctk.CTkFont(size=12),
                    width=w,
                    anchor="w",
                ).grid(row=0, column=col, padx=(10 if col == 0 else 4),
                       pady=4, sticky="w")

    def _update_timestamp(self):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self._last_updated.configure(text=f"Updated {now}")

    # ── Cleanup on destroy ────────────────────────────────────────────────────
    def destroy(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()