import customtkinter as ctk
from services.product_service import ProductService


# ── Add / Edit modal dialog ───────────────────────────────────────────────────
class ProductFormDialog(ctk.CTkToplevel):
    """Modal form for creating or editing a product."""

    def __init__(self, parent, product=None, categories=None, on_save=None):
        super().__init__(parent)
        self._product    = product
        self._categories = categories or []
        self._on_save    = on_save
        self._is_edit    = product is not None

        self.title("Edit Product" if self._is_edit else "Add Product")
        self.geometry("700x700")
        self.resizable(False, False)
        self.grab_set()   # modal behaviour
        self.lift()

        self._build_ui()

        if self._is_edit:
            self._populate(product)

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Edit Product" if self._is_edit else "Add New Product",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 16))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=28)

        def field(label, widget_fn):
            ctk.CTkLabel(form, text=label, anchor="w").pack(
                fill="x", pady=(8, 2)
            )
            w = widget_fn()
            w.pack(fill="x")
            return w

        self._name_entry = field("Product Name *", lambda: ctk.CTkEntry(
            form, placeholder_text="e.g. Coca-Cola 500ml", height=38))

        # Category dropdown
        ctk.CTkLabel(form, text="Category", anchor="w").pack(
            fill="x", pady=(8, 2))
        cat_names = ["(None)"] + [c["name"] for c in self._categories]
        self._cat_var = ctk.StringVar(value=cat_names[0])
        self._cat_menu = ctk.CTkOptionMenu(
            form, values=cat_names, variable=self._cat_var, height=38
        )
        self._cat_menu.pack(fill="x")

        self._price_entry = field("Price (GH₵) *", lambda: ctk.CTkEntry(
            form, placeholder_text="0.00", height=38))

        self._qty_entry = field("Quantity *", lambda: ctk.CTkEntry(
            form, placeholder_text="0", height=38))

        self._barcode_entry = field("Barcode", lambda: ctk.CTkEntry(
            form, placeholder_text="optional", height=38))

        self._low_stock_entry = field("Low Stock Alert Qty *", lambda: ctk.CTkEntry(
            form, placeholder_text="5", height=38))

        # Error label
        self._error = ctk.CTkLabel(
            self, text="", text_color="#e05252", font=ctk.CTkFont(size=12)
        )
        self._error.pack(pady=(8, 0))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(8, 24))

        ctk.CTkButton(
            btn_row, text="Cancel", width=120, height=40,
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Save Product", width=160, height=40,
            command=self._submit,
        ).pack(side="right")

    def _populate(self, p):
        self._name_entry.insert(0, p.name)
        self._price_entry.insert(0, str(p.price))
        self._qty_entry.insert(0, str(p.quantity))
        self._barcode_entry.insert(0, p.barcode or "")
        self._low_stock_entry.insert(0, str(p.low_stock_qty))

        if p.category_name:
            self._cat_var.set(p.category_name)

    # ── Submit ────────────────────────────────────────────────────────────────
    def _submit(self):
        name     = self._name_entry.get().strip()
        price_s  = self._price_entry.get().strip()
        qty_s    = self._qty_entry.get().strip()
        barcode  = self._barcode_entry.get().strip()
        low_s    = self._low_stock_entry.get().strip()
        cat_name = self._cat_var.get()

        # Validation
        if not name:
            self._error.configure(text="Product name is required.")
            return
        try:
            price = float(price_s)
            if price < 0:
                raise ValueError
        except ValueError:
            self._error.configure(text="Enter a valid price (e.g. 4.99).")
            return
        try:
            qty = int(qty_s)
            if qty < 0:
                raise ValueError
        except ValueError:
            self._error.configure(text="Quantity must be a whole number ≥ 0.")
            return
        try:
            low_stock = int(low_s)
        except ValueError:
            self._error.configure(text="Low stock qty must be a whole number.")
            return

        # Resolve category id
        cat_id = None
        for c in self._categories:
            if c["name"] == cat_name:
                cat_id = c["id"]
                break

        if self._on_save:
            self._on_save(
                name, cat_id, price, qty,
                barcode or None, low_stock
            )
        self.destroy()


# ── Main product view ─────────────────────────────────────────────────────────
class ProductView(ctk.CTkFrame):

    COLUMNS = [
        ("ID",        50),
        ("Name",     220),
        ("Category", 130),
        ("Price",     90),
        ("Qty",       70),
        ("Barcode",  130),
        ("Actions",  160),
    ]

    def __init__(self, parent, current_user):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._svc  = ProductService()
        self._user = current_user
        self._build_ui()
        self._load_products()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text="Products",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="＋  Add Product",
            width=140,
            height=36,
            corner_radius=8,
            command=self._open_add_dialog,
        ).pack(side="right")

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=24, pady=12)

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load_products())

        ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍  Search by name or barcode…",
            textvariable=self._search_var,
            height=38,
            corner_radius=8,
        ).pack(fill="x")

        # Table header
        table_wrap = ctk.CTkFrame(self, corner_radius=12)
        table_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        header_row = ctk.CTkFrame(
            table_wrap, fg_color=("gray80", "gray25"), corner_radius=8
        )
        header_row.pack(fill="x", padx=8, pady=(8, 0))

        for col, (label, width) in enumerate(self.COLUMNS):
            ctk.CTkLabel(
                header_row,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width,
                anchor="w",
            ).grid(row=0, column=col, padx=(10 if col == 0 else 4),
                   pady=8, sticky="w")

        # Scrollable rows
        self._rows_frame = ctk.CTkScrollableFrame(
            table_wrap, fg_color="transparent", corner_radius=0
        )
        self._rows_frame.pack(fill="both", expand=True, padx=8, pady=4)

    # ── Data ──────────────────────────────────────────────────────────────────
    def _load_products(self):
        search = self._search_var.get() if hasattr(self, "_search_var") else ""
        products = self._svc.get_all(search)

        for w in self._rows_frame.winfo_children():
            w.destroy()

        if not products:
            ctk.CTkLabel(
                self._rows_frame,
                text="No products found.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, p in enumerate(products):
            is_low = p.quantity <= p.low_stock_qty
            bg = ("#fff0f0", "#3a1a1a") if is_low else (
                ("gray92", "gray17") if i % 2 == 0 else ("gray86", "gray20")
            )

            row = ctk.CTkFrame(
                self._rows_frame, fg_color=bg, corner_radius=6, height=38
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            qty_color = ("#c0392b", "#e05252") if is_low else (
                "gray10", "gray90"
            )

            values = [
                (f"#{p.id}",                   None),
                (p.name,                        None),
                (p.category_name or "—",        None),
                (f"GH₵ {p.price:,.2f}",         None),
                (str(p.quantity),               qty_color),
                (p.barcode or "—",              None),
            ]

            for col, (val, color) in enumerate(values):
                lbl = ctk.CTkLabel(
                    row,
                    text=val,
                    font=ctk.CTkFont(size=12),
                    width=self.COLUMNS[col][1],
                    anchor="w",
                )
                if color:
                    lbl.configure(text_color=color)
                lbl.grid(row=0, column=col,
                         padx=(10 if col == 0 else 4), pady=4, sticky="w")

            # Action buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=6, padx=4, pady=3, sticky="w")

            ctk.CTkButton(
                btn_frame,
                text="Edit",
                width=62,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda pid=p.id: self._open_edit_dialog(pid),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                btn_frame,
                text="Delete",
                width=62,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color="#c0392b",
                hover_color="#922b21",
                command=lambda pid=p.id, pname=p.name: self._confirm_delete(
                    pid, pname
                ),
            ).pack(side="left")

    # ── Dialogs ───────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        cats = self._svc.get_categories()
        ProductFormDialog(
            self,
            categories=cats,
            on_save=self._save_new_product,
        )

    def _open_edit_dialog(self, product_id: int):
        product = self._svc.get_by_id(product_id)
        cats    = self._svc.get_categories()
        if product:
            ProductFormDialog(
                self,
                product=product,
                categories=cats,
                on_save=lambda *args: self._save_edit_product(product_id, *args),
            )

    def _save_new_product(self, name, cat_id, price, qty, barcode, low_stock):
        ok, msg = self._svc.create(name, cat_id, price, qty, barcode, low_stock)
        if ok:
            self._load_products()
        else:
            self._show_error(msg)

    def _save_edit_product(self, product_id, name, cat_id, price,
                           qty, barcode, low_stock):
        ok, msg = self._svc.update(
            product_id, name, cat_id, price, qty, barcode, low_stock
        )
        if ok:
            self._load_products()
        else:
            self._show_error(msg)

    def _confirm_delete(self, product_id: int, name: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Delete")
        dialog.geometry("360x180")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.lift()

        ctk.CTkLabel(
            dialog,
            text=f"Delete  '{name}'?",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(28, 6))

        ctk.CTkLabel(
            dialog,
            text="This action cannot be undone.",
            text_color="gray50",
            font=ctk.CTkFont(size=12),
        ).pack()

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=20)

        ctk.CTkButton(
            btn_row, text="Cancel", width=110, height=38,
            fg_color="transparent", border_width=1,
            command=dialog.destroy,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row, text="Yes, Delete", width=130, height=38,
            fg_color="#c0392b", hover_color="#922b21",
            command=lambda: [
                self._svc.delete(product_id),
                self._load_products(),
                dialog.destroy(),
            ],
        ).pack(side="left", padx=8)

    def _show_error(self, message: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("340x140")
        dialog.resizable(False, False)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text=message, wraplength=300).pack(pady=30)
        ctk.CTkButton(dialog, text="OK", width=100,
                      command=dialog.destroy).pack()