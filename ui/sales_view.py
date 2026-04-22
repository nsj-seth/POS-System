import customtkinter as ctk
from services.product_service import ProductService
from models.cart import Cart


class SalesView(ctk.CTkFrame):
    """POS sales screen — product browser + live cart."""

    def __init__(self, parent, current_user, on_checkout=None):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._svc         = ProductService()
        self._user        = current_user
        self._cart        = Cart()
        self._on_checkout = on_checkout   # callback → payment screen

        self._build_ui()
        self._load_products()

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Page title
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.pack(fill="x", padx=24, pady=(20, 12))
        ctk.CTkLabel(
            title_bar,
            text="New Sale",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        # Two-column layout
        columns = ctk.CTkFrame(self, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        columns.grid_columnconfigure(0, weight=3)
        columns.grid_columnconfigure(1, weight=2)
        columns.grid_rowconfigure(0, weight=1)

        self._build_product_panel(columns)
        self._build_cart_panel(columns)

    # ── Left panel: product browser ───────────────────────────────────────────
    def _build_product_panel(self, parent):
        panel = ctk.CTkFrame(parent, corner_radius=12)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Search
        ctk.CTkLabel(
            panel,
            text="Products",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(14, 6))

        self._prod_search = ctk.StringVar()
        self._prod_search.trace_add("write", lambda *_: self._load_products())
        ctk.CTkEntry(
            panel,
            placeholder_text="🔍  Search name or barcode…",
            textvariable=self._prod_search,
            height=36,
            corner_radius=8,
        ).pack(fill="x", padx=14, pady=(0, 8))

        # Product grid (scrollable)
        self._prod_frame = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", corner_radius=0
        )
        self._prod_frame.pack(fill="both", expand=True, padx=6, pady=(0, 8))
        self._prod_frame.grid_columnconfigure((0, 1, 2), weight=1)

    # ── Right panel: cart ─────────────────────────────────────────────────────
    def _build_cart_panel(self, parent):
        panel = ctk.CTkFrame(parent, corner_radius=12)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text="Cart",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(14, 6))

        # Cart items (scrollable)
        self._cart_frame = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", corner_radius=0, height=300
        )
        self._cart_frame.pack(fill="both", expand=True, padx=6)

        # ── Totals section ────────────────────────────────────────────────────
        totals = ctk.CTkFrame(panel, fg_color=("gray85", "gray20"),
                              corner_radius=10)
        totals.pack(fill="x", padx=10, pady=10)

        def total_row(label, key, bold=False):
            row = ctk.CTkFrame(totals, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(size=13,
                                 weight="bold" if bold else "normal"),
                anchor="w",
            ).pack(side="left")
            lbl = ctk.CTkLabel(
                row,
                text="GH₵ 0.00",
                font=ctk.CTkFont(size=13,
                                 weight="bold" if bold else "normal"),
                anchor="e",
            )
            lbl.pack(side="right")
            return lbl

        self._subtotal_lbl  = total_row("Subtotal",  "sub")
        self._discount_lbl  = total_row("Discount",  "disc")
        self._total_lbl     = total_row("TOTAL",     "total", bold=True)

        # Discount entry
        disc_row = ctk.CTkFrame(totals, fg_color="transparent")
        disc_row.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(
            disc_row, text="Discount (GH₵):", font=ctk.CTkFont(size=12)
        ).pack(side="left")

        self._discount_entry = ctk.CTkEntry(
            disc_row, width=90, height=30, placeholder_text="0.00"
        )
        self._discount_entry.pack(side="right")
        self._discount_entry.bind("<KeyRelease>", self._on_discount_change)

        # Clear cart button
        ctk.CTkButton(
            panel,
            text="🗑  Clear Cart",
            height=34,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            text_color=("#c0392b", "#e05252"),
            hover_color=("#fdecea", "#3a1a1a"),
            command=self._clear_cart,
        ).pack(fill="x", padx=10, pady=(0, 6))

        # Checkout button
        self._checkout_btn = ctk.CTkButton(
            panel,
            text="Proceed to Payment  →",
            height=46,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            state="disabled",
            command=self._proceed_to_checkout,
        )
        self._checkout_btn.pack(fill="x", padx=10, pady=(0, 14))

    # ══════════════════════════════════════════════════════════════════════════
    #  PRODUCT GRID
    # ══════════════════════════════════════════════════════════════════════════
    def _load_products(self):
        search = self._prod_search.get() if hasattr(self, "_prod_search") else ""
        products = self._svc.get_all(search)

        for w in self._prod_frame.winfo_children():
            w.destroy()

        if not products:
            ctk.CTkLabel(
                self._prod_frame,
                text="No products found.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, p in enumerate(products):
            col = i % 3
            row = i // 3
            self._make_product_card(p, row, col)

    def _make_product_card(self, product, row, col):
        out_of_stock = product.quantity == 0
        card = ctk.CTkFrame(
            self._prod_frame,
            corner_radius=10,
            fg_color=("gray88", "gray22"),
            border_width=1,
            border_color=("gray75", "gray35"),
        )
        card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

        ctk.CTkLabel(
            card,
            text=product.name,
            font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=140,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 2))

        ctk.CTkLabel(
            card,
            text=f"GH₵ {product.price:,.2f}",
            font=ctk.CTkFont(size=13),
            text_color=("#1a7abf", "#4da6e8"),
            anchor="w",
        ).pack(fill="x", padx=10)

        stock_color = ("#c0392b", "#e05252") if out_of_stock else "gray50"
        stock_text  = "Out of stock" if out_of_stock else f"Stock: {product.quantity}"
        ctk.CTkLabel(
            card,
            text=stock_text,
            font=ctk.CTkFont(size=11),
            text_color=stock_color,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(
            card,
            text="Add to Cart",
            height=30,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            state="disabled" if out_of_stock else "normal",
            command=lambda p=product: self._add_to_cart(p),
        ).pack(fill="x", padx=10, pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════════════
    #  CART LOGIC
    # ══════════════════════════════════════════════════════════════════════════
    def _add_to_cart(self, product):
        try:
            self._cart.add_item(product)
            self._refresh_cart()
        except ValueError as e:
            self._show_toast(str(e))

    def _refresh_cart(self):
        for w in self._cart_frame.winfo_children():
            w.destroy()

        if self._cart.is_empty():
            ctk.CTkLabel(
                self._cart_frame,
                text="Cart is empty.\nAdd products from the left.",
                text_color="gray50",
                justify="center",
            ).pack(pady=30)
            self._checkout_btn.configure(state="disabled")
        else:
            for item in self._cart.items:
                self._make_cart_row(item)
            self._checkout_btn.configure(state="normal")

        self._update_totals()

    def _make_cart_row(self, item):
        row = ctk.CTkFrame(
            self._cart_frame,
            corner_radius=8,
            fg_color=("gray90", "gray20"),
        )
        row.pack(fill="x", pady=3, padx=2)

        # Product name + subtotal
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            info,
            text=item.product.name,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            wraplength=180,
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info,
            text=f"GH₵ {item.subtotal:,.2f}",
            font=ctk.CTkFont(size=12),
            anchor="e",
        ).pack(side="right")

        # Quantity controls
        ctrl = ctk.CTkFrame(row, fg_color="transparent")
        ctrl.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkLabel(
            ctrl,
            text=f"@ GH₵ {item.unit_price:,.2f}",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            anchor="w",
        ).pack(side="left")

        # Qty stepper
        stepper = ctk.CTkFrame(ctrl, fg_color="transparent")
        stepper.pack(side="right")

        ctk.CTkButton(
            stepper, text="−", width=28, height=28,
            corner_radius=6, font=ctk.CTkFont(size=14),
            command=lambda pid=item.product.id,
                           qty=item.quantity: self._change_qty(pid, qty - 1),
        ).pack(side="left", padx=2)

        ctk.CTkLabel(
            stepper,
            text=str(item.quantity),
            font=ctk.CTkFont(size=13, weight="bold"),
            width=28,
        ).pack(side="left")

        ctk.CTkButton(
            stepper, text="＋", width=28, height=28,
            corner_radius=6, font=ctk.CTkFont(size=14),
            command=lambda pid=item.product.id,
                           qty=item.quantity: self._change_qty(pid, qty + 1),
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            stepper, text="🗑", width=28, height=28,
            corner_radius=6,
            fg_color="transparent",
            text_color=("#c0392b", "#e05252"),
            command=lambda pid=item.product.id: self._remove_item(pid),
        ).pack(side="left", padx=(6, 0))

    def _change_qty(self, product_id: int, new_qty: int):
        try:
            self._cart.update_quantity(product_id, new_qty)
            self._refresh_cart()
        except ValueError as e:
            self._show_toast(str(e))

    def _remove_item(self, product_id: int):
        self._cart.remove_item(product_id)
        self._refresh_cart()

    def _clear_cart(self):
        self._cart.clear()
        self._discount_entry.delete(0, "end")
        self._refresh_cart()

    def _on_discount_change(self, _event=None):
        try:
            val = float(self._discount_entry.get())
            self._cart.discount = max(0.0, val)
        except ValueError:
            self._cart.discount = 0.0
        self._update_totals()

    def _update_totals(self):
        self._subtotal_lbl.configure(
            text=f"GH₵ {self._cart.subtotal:,.2f}"
        )
        self._discount_lbl.configure(
            text=f"− GH₵ {self._cart.discount_amount:,.2f}"
        )
        self._total_lbl.configure(
            text=f"GH₵ {self._cart.total:,.2f}"
        )

    # ── Checkout ──────────────────────────────────────────────────────────────
    def _proceed_to_checkout(self):
        if self._on_checkout:
            self._on_checkout(self._cart)

    # ── Toast notification ────────────────────────────────────────────────────
    def _show_toast(self, message: str):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(size=12),
            fg_color=("#c0392b", "#922b21"),
            corner_radius=8,
            padx=16,
            pady=10,
        ).pack()

        # Position near top-right of main window
        x = self.winfo_rootx() + self.winfo_width() - 340
        y = self.winfo_rooty() + 60
        toast.geometry(f"+{x}+{y}")
        toast.after(2500, toast.destroy)