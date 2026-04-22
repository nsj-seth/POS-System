import customtkinter as ctk
from datetime import datetime, timedelta
from services.report_service import ReportService


class ReportsView(ctk.CTkFrame):
    """Reports screen with Daily Sales and Inventory tabs."""

    def __init__(self, parent, current_user):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._user = current_user
        self._svc  = ReportService()
        self._selected_date = datetime.now().strftime("%Y-%m-%d")

        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    #  SKELETON
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Page header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkLabel(
            header,
            text="Reports",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        # Tab buttons
        self._tab_var = ctk.StringVar(value="daily")
        tab_frame = ctk.CTkFrame(header, fg_color="transparent")
        tab_frame.pack(side="right")

        for label, value in [("📅  Daily Sales", "daily"),
                              ("📦  Inventory",   "inventory")]:
            ctk.CTkButton(
                tab_frame,
                text=label,
                width=150,
                height=34,
                corner_radius=8,
                fg_color=("gray80", "gray30"),
                hover_color=("gray70", "gray40"),
                text_color=("gray10", "gray90"),
                command=lambda v=value: self._switch_tab(v),
            ).pack(side="left", padx=4)

        # Content container
        self._tab_content = ctk.CTkFrame(
            self, fg_color="transparent"
        )
        self._tab_content.pack(
            fill="both", expand=True, padx=24, pady=(0, 24)
        )

        # Load default tab
        self._switch_tab("daily")

    def _switch_tab(self, tab: str):
        self._tab_var.set(tab)
        for w in self._tab_content.winfo_children():
            w.destroy()

        if tab == "daily":
            self._build_daily_tab()
        else:
            self._build_inventory_tab()

    # ══════════════════════════════════════════════════════════════════════════
    #  DAILY SALES TAB
    # ══════════════════════════════════════════════════════════════════════════
    def _build_daily_tab(self):
        parent = self._tab_content

        # ── Date picker row ───────────────────────────────────────────────────
        date_row = ctk.CTkFrame(parent, fg_color="transparent")
        date_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            date_row, text="Date:",
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 8))

        self._date_entry = ctk.CTkEntry(
            date_row, width=130, height=34,
            placeholder_text="YYYY-MM-DD",
        )
        self._date_entry.insert(0, self._selected_date)
        self._date_entry.pack(side="left", padx=(0, 8))

        # Quick date buttons
        for label, delta in [("Today", 0), ("Yesterday", -1),
                              ("2 days ago", -2)]:
            d = (datetime.now() + timedelta(days=delta)).strftime("%Y-%m-%d")
            ctk.CTkButton(
                date_row, text=label, width=100, height=34,
                corner_radius=8,
                fg_color=("gray80", "gray30"),
                hover_color=("gray70", "gray40"),
                text_color=("gray10", "gray90"),
                command=lambda date=d: self._set_date(date),
            ).pack(side="left", padx=4)

        ctk.CTkButton(
            date_row, text="Load Report", width=120, height=34,
            corner_radius=8,
            command=self._load_daily_report,
        ).pack(side="left", padx=(8, 0))

        # Export button
        ctk.CTkButton(
            date_row, text="⬇  Export CSV", width=120, height=34,
            corner_radius=8,
            fg_color=("#1e8449", "#1e8449"),
            hover_color=("#145a32", "#145a32"),
            command=self._export_daily_csv,
        ).pack(side="right")

        # ── Summary stat cards ────────────────────────────────────────────────
        self._daily_cards_frame = ctk.CTkFrame(
            parent, fg_color="transparent"
        )
        self._daily_cards_frame.pack(fill="x", pady=(0, 12))

        # ── Two column lower section ──────────────────────────────────────────
        lower = ctk.CTkFrame(parent, fg_color="transparent")
        lower.pack(fill="both", expand=True)
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=1)
        lower.grid_rowconfigure(0, weight=1)

        # Transactions table
        left_panel = ctk.CTkFrame(lower, corner_radius=12)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            left_panel,
            text="Transactions",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 6))

        t_headers = [
            ("ID", 48), ("Customer", 150), ("Cashier", 100),
            ("Total", 100), ("Discount", 90),
            ("Method", 110), ("Items", 50), ("Time", 130),
        ]
        t_hdr = ctk.CTkFrame(
            left_panel,
            fg_color=("gray80", "gray25"), corner_radius=8
        )
        t_hdr.pack(fill="x", padx=8)

        for col, (h, w) in enumerate(t_headers):
            ctk.CTkLabel(
                t_hdr, text=h,
                font=ctk.CTkFont(size=11, weight="bold"),
                width=w, anchor="w",
            ).grid(row=0, column=col,
                   padx=(8 if col == 0 else 3), pady=6, sticky="w")

        self._trans_frame = ctk.CTkScrollableFrame(
            left_panel, fg_color="transparent", corner_radius=0
        )
        self._trans_frame.pack(
            fill="both", expand=True, padx=8, pady=4
        )
        self._t_headers = t_headers

        # Top products panel
        right_panel = ctk.CTkFrame(lower, corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            right_panel,
            text="Top Products",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(12, 8))

        self._top_prod_frame = ctk.CTkScrollableFrame(
            right_panel, fg_color="transparent", corner_radius=0
        )
        self._top_prod_frame.pack(
            fill="both", expand=True, padx=8, pady=(0, 8)
        )

        # Load data for today
        self._load_daily_report()

    def _set_date(self, date_str: str):
        self._date_entry.delete(0, "end")
        self._date_entry.insert(0, date_str)
        self._selected_date = date_str
        self._load_daily_report()

    def _load_daily_report(self):
        date_str = self._date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return
        self._selected_date = date_str
        data = self._svc.get_daily_summary(date_str)

        self._update_daily_cards(data["summary"])
        self._update_transactions(data["transactions"])
        self._update_top_products(data["top_products"])

    def _update_daily_cards(self, s: dict):
        for w in self._daily_cards_frame.winfo_children():
            w.destroy()

        cards = [
            ("🛍️",  "Transactions",    str(s["total_transactions"])),
            ("💰",  "Revenue",
             f"GH₵ {s['total_revenue']:,.2f}"),
            ("🏷️",  "Discounts Given",
             f"GH₵ {s['total_discounts']:,.2f}"),
            ("📊",  "Avg Sale Value",
             f"GH₵ {s['avg_sale_value']:,.2f}"),
            ("💵",  "Cash Sales",
             f"{s['cash_count']}  (GH₵ {s['cash_revenue']:,.2f})"),
            ("📱",  "MoMo Sales",
             f"{s['momo_count']}  (GH₵ {s['momo_revenue']:,.2f})"),
        ]

        for i, (icon, label, value) in enumerate(cards):
            card = ctk.CTkFrame(
                self._daily_cards_frame,
                corner_radius=10, height=80,
            )
            card.grid(row=0, column=i, padx=5, sticky="ew")
            self._daily_cards_frame.grid_columnconfigure(i, weight=1)
            card.pack_propagate(False)

            ctk.CTkLabel(
                card,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(size=11),
                text_color="gray50",
                anchor="w",
            ).pack(fill="x", padx=12, pady=(10, 0))

            ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            ).pack(fill="x", padx=12)

    def _update_transactions(self, rows: list):
        for w in self._trans_frame.winfo_children():
            w.destroy()

        if not rows:
            ctk.CTkLabel(
                self._trans_frame,
                text="No transactions on this date.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, t in enumerate(rows):
            bg = ("gray92", "gray17") if i % 2 == 0 \
                else ("gray86", "gray20")
            row = ctk.CTkFrame(
                self._trans_frame, fg_color=bg,
                corner_radius=6, height=32,
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            time_str = t["created_at"][11:16]
            vals = [
                (f"#{t['id']}",                              48),
                (t["customer"],                              150),
                (t["cashier"] or "—",                        100),
                (f"GH₵ {t['total_amount']:,.2f}",            100),
                (f"GH₵ {t['discount_amount']:,.2f}",          90),
                (t["payment_method"].replace(
                    "_", " ").title(),                        110),
                (str(t["item_count"]),                        50),
                (time_str,                                   130),
            ]
            for col, (v, w) in enumerate(vals):
                ctk.CTkLabel(
                    row, text=v,
                    font=ctk.CTkFont(size=11),
                    width=w, anchor="w",
                ).grid(row=0, column=col,
                       padx=(8 if col == 0 else 3),
                       pady=3, sticky="w")

    def _update_top_products(self, rows: list):
        for w in self._top_prod_frame.winfo_children():
            w.destroy()

        if not rows:
            ctk.CTkLabel(
                self._top_prod_frame,
                text="No data.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, p in enumerate(rows):
            card = ctk.CTkFrame(
                self._top_prod_frame,
                fg_color=("gray90", "gray20"),
                corner_radius=8,
            )
            card.pack(fill="x", pady=3, padx=2)

            ctk.CTkLabel(
                card,
                text=f"{i+1}.  {p['name'] or 'Unknown'}",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(fill="x", padx=12, pady=(8, 2))

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=12, pady=(0, 8))

            ctk.CTkLabel(
                info,
                text=f"{p['units_sold']} units sold",
                font=ctk.CTkFont(size=11),
                text_color="gray50",
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                info,
                text=f"GH₵ {p['revenue']:,.2f}",
                font=ctk.CTkFont(size=11),
                anchor="e",
            ).pack(side="right")

    def _export_daily_csv(self):
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"sales_{self._selected_date}.csv",
        )
        if path:
            ok, msg = self._svc.export_daily_csv(
                self._selected_date, path
            )
            self._show_export_toast(ok, msg)

    # ══════════════════════════════════════════════════════════════════════════
    #  INVENTORY TAB
    # ══════════════════════════════════════════════════════════════════════════
    def _build_inventory_tab(self):
        parent = self._tab_content

        # Controls row
        ctrl = ctk.CTkFrame(parent, fg_color="transparent")
        ctrl.pack(fill="x", pady=(0, 12))

        self._inv_search = ctk.StringVar()
        self._inv_search.trace_add(
            "write", lambda *_: self._load_inventory()
        )
        ctk.CTkEntry(
            ctrl,
            placeholder_text="🔍  Search products…",
            textvariable=self._inv_search,
            height=34, width=260,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl, text="↻  Refresh", width=100, height=34,
            corner_radius=8,
            command=self._load_inventory,
        ).pack(side="left")

        ctk.CTkButton(
            ctrl, text="⬇  Export CSV", width=120, height=34,
            corner_radius=8,
            fg_color=("#1e8449", "#1e8449"),
            hover_color=("#145a32", "#145a32"),
            command=self._export_inventory_csv,
        ).pack(side="right")

        # Stat cards
        self._inv_cards_frame = ctk.CTkFrame(
            parent, fg_color="transparent"
        )
        self._inv_cards_frame.pack(fill="x", pady=(0, 12))

        # Table
        wrap = ctk.CTkFrame(parent, corner_radius=12)
        wrap.pack(fill="both", expand=True)

        inv_headers = [
            ("ID", 45), ("Name", 200), ("Category", 120),
            ("Price", 90), ("Qty", 65), ("Low Stock", 85),
            ("Stock Value", 110), ("Total Sold", 90),
        ]
        hdr = ctk.CTkFrame(
            wrap, fg_color=("gray80", "gray25"), corner_radius=8
        )
        hdr.pack(fill="x", padx=8, pady=(8, 0))

        for col, (h, w) in enumerate(inv_headers):
            ctk.CTkLabel(
                hdr, text=h,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=w, anchor="w",
            ).grid(row=0, column=col,
                   padx=(10 if col == 0 else 4),
                   pady=8, sticky="w")

        self._inv_rows_frame = ctk.CTkScrollableFrame(
            wrap, fg_color="transparent", corner_radius=0
        )
        self._inv_rows_frame.pack(
            fill="both", expand=True, padx=8, pady=4
        )
        self._inv_headers = inv_headers

        self._load_inventory()

    def _load_inventory(self):
        search = self._inv_search.get() \
            if hasattr(self, "_inv_search") else ""
        data = self._svc.get_inventory_report(search)

        self._update_inv_cards(data["stats"])
        self._update_inv_table(data["products"])

    def _update_inv_cards(self, s: dict):
        for w in self._inv_cards_frame.winfo_children():
            w.destroy()

        cards = [
            ("📦", "Total Products",  str(s["total_products"] or 0), None),
            ("🔢", "Total Units",     str(s["total_units"]    or 0), None),
            ("💰", "Stock Value",
             f"GH₵ {(s['stock_value'] or 0):,.2f}",              None),
            ("⚠️", "Low Stock Items",
             str(s["low_stock_count"] or 0),                   "#c0392b"),
            ("🚫", "Out of Stock",
             str(s["out_of_stock"]    or 0),                   "#c0392b"),
        ]

        for i, (icon, label, value, color) in enumerate(cards):
            card = ctk.CTkFrame(
                self._inv_cards_frame,
                corner_radius=10, height=80,
            )
            card.grid(row=0, column=i, padx=5, sticky="ew")
            self._inv_cards_frame.grid_columnconfigure(i, weight=1)
            card.pack_propagate(False)

            ctk.CTkLabel(
                card,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(size=11),
                text_color="gray50",
                anchor="w",
            ).pack(fill="x", padx=12, pady=(10, 0))

            lbl = ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=18, weight="bold"),
                anchor="w",
            )
            if color:
                lbl.configure(text_color=color)
            lbl.pack(fill="x", padx=12)

    def _update_inv_table(self, products: list):
        for w in self._inv_rows_frame.winfo_children():
            w.destroy()

        if not products:
            ctk.CTkLabel(
                self._inv_rows_frame,
                text="No products found.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, p in enumerate(products):
            is_low  = p["quantity"] <= p["low_stock_qty"]
            is_zero = p["quantity"] == 0

            if is_zero:
                bg = ("#fff0f0", "#3a1a1a")
            elif is_low:
                bg = ("#fff8e1", "#2e2a10")
            else:
                bg = ("gray92", "gray17") if i % 2 == 0 \
                    else ("gray86", "gray20")

            row = ctk.CTkFrame(
                self._inv_rows_frame, fg_color=bg,
                corner_radius=6, height=36,
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            qty_color = (
                ("#c0392b", "#e05252") if is_zero else
                ("#b7770d", "#f0a500") if is_low  else
                ("gray10",  "gray90")
            )

            stock_val = p["price"] * p["quantity"]
            vals = [
                (f"#{p['id']}",                       45,  None),
                (p["name"],                           200,  None),
                (p["category_name"] or "—",           120,  None),
                (f"GH₵ {p['price']:,.2f}",             90,  None),
                (str(p["quantity"]),                   65,  qty_color),
                (str(p["low_stock_qty"]),              85,  None),
                (f"GH₵ {stock_val:,.2f}",             110,  None),
                (str(p["total_sold"]),                 90,  None),
            ]

            for col, (v, w, color) in enumerate(vals):
                lbl = ctk.CTkLabel(
                    row, text=v,
                    font=ctk.CTkFont(size=12),
                    width=w, anchor="w",
                )
                if color:
                    lbl.configure(text_color=color)
                lbl.grid(row=0, column=col,
                         padx=(10 if col == 0 else 4),
                         pady=4, sticky="w")

    def _export_inventory_csv(self):
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="inventory_report.csv",
        )
        if path:
            ok, msg = self._svc.export_inventory_csv(path)
            self._show_export_toast(ok, msg)

    # ── Toast ─────────────────────────────────────────────────────────────────
    def _show_export_toast(self, ok: bool, msg: str):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        color = ("#1e8449", "#145a32") if ok else ("#c0392b", "#922b21")
        ctk.CTkLabel(
            toast, text=msg,
            font=ctk.CTkFont(size=12),
            fg_color=color,
            corner_radius=8,
            padx=16, pady=10,
        ).pack()

        x = self.winfo_rootx() + self.winfo_width() - 420
        y = self.winfo_rooty() + 60
        toast.geometry(f"+{x}+{y}")
        toast.after(3000, toast.destroy)