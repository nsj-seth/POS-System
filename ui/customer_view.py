import customtkinter as ctk
from services.customer_service import CustomerService


# ── Add / Edit dialog ─────────────────────────────────────────────────────────
class CustomerFormDialog(ctk.CTkToplevel):

    def __init__(self, parent, customer=None, on_save=None):
        super().__init__(parent)
        self._customer = customer
        self._on_save  = on_save
        self._is_edit  = customer is not None

        self.title("Edit Customer" if self._is_edit else "Add Customer")
        self.geometry("400x380")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self._build_ui()
        if self._is_edit:
            self._populate()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Edit Customer" if self._is_edit else "Add New Customer",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 16))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=28)

        def field(label, placeholder):
            ctk.CTkLabel(form, text=label, anchor="w").pack(
                fill="x", pady=(8, 2)
            )
            entry = ctk.CTkEntry(
                form, placeholder_text=placeholder, height=38, corner_radius=8
            )
            entry.pack(fill="x")
            return entry

        self._name_entry  = field("Full Name *",     "e.g. Kwame Mensah")
        self._phone_entry = field("Phone Number",    "e.g. 024 000 0000")
        self._email_entry = field("Email Address",   "e.g. kwame@email.com")

        self._error = ctk.CTkLabel(
            self, text="", text_color="#e05252",
            font=ctk.CTkFont(size=12)
        )
        self._error.pack(pady=(10, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(8, 24))

        ctk.CTkButton(
            btn_row, text="Cancel", width=110, height=40,
            fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Save Customer", width=150, height=40,
            command=self._submit,
        ).pack(side="right")

    def _populate(self):
        self._name_entry.insert(0,  self._customer.name)
        self._phone_entry.insert(0, self._customer.phone or "")
        self._email_entry.insert(0, self._customer.email or "")

    def _submit(self):
        name  = self._name_entry.get().strip()
        phone = self._phone_entry.get().strip()
        email = self._email_entry.get().strip()

        if not name:
            self._error.configure(text="Full name is required.")
            return

        if self._on_save:
            self._on_save(name, phone or None, email or None)
        self.destroy()


# ── Purchase history dialog ───────────────────────────────────────────────────
class PurchaseHistoryDialog(ctk.CTkToplevel):

    def __init__(self, parent, customer, history: list[dict]):
        super().__init__(parent)
        self.title(f"Purchase History — {customer.name}")
        self.geometry("600x460")
        self.grab_set()
        self.lift()

        ctk.CTkLabel(
            self,
            text=f"Purchase History: {customer.name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text=f"{customer.total_purchases} purchases  •  "
                 f"Total spent: GH₵ {customer.total_spent:,.2f}",
            font=ctk.CTkFont(size=12),
            text_color="gray50",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(0, 12))

        # Table header
        wrap = ctk.CTkFrame(self, corner_radius=10)
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        hdr = ctk.CTkFrame(wrap, fg_color=("gray80", "gray25"), corner_radius=8)
        hdr.pack(fill="x", padx=8, pady=(8, 0))

        headers = [("ID", 50), ("Amount", 120),
                   ("Method", 130), ("Cashier", 110), ("Date", 160)]
        for col, (h, w) in enumerate(headers):
            ctk.CTkLabel(
                hdr, text=h,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=w, anchor="w",
            ).grid(row=0, column=col,
                   padx=(10 if col == 0 else 4), pady=8, sticky="w")

        scroll = ctk.CTkScrollableFrame(
            wrap, fg_color="transparent", corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=8, pady=4)

        if not history:
            ctk.CTkLabel(
                scroll, text="No purchases yet.",
                text_color="gray50"
            ).pack(pady=20)
        else:
            for i, sale in enumerate(history):
                bg = ("gray92", "gray17") if i % 2 == 0 \
                    else ("gray86", "gray20")
                row = ctk.CTkFrame(
                    scroll, fg_color=bg, corner_radius=6, height=34
                )
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)

                time_str = sale["created_at"][:16].replace("T", "  ")
                vals = [
                    (f"#{sale['id']}",                           50),
                    (f"GH₵ {sale['total_amount']:,.2f}",         120),
                    (sale["payment_method"].replace(
                        "_", " ").title(),                        130),
                    (sale["cashier"] or "—",                     110),
                    (time_str,                                    160),
                ]
                for col, (v, w) in enumerate(vals):
                    ctk.CTkLabel(
                        row, text=v,
                        font=ctk.CTkFont(size=12),
                        width=w, anchor="w",
                    ).grid(row=0, column=col,
                           padx=(10 if col == 0 else 4),
                           pady=4, sticky="w")

        ctk.CTkButton(
            self, text="Close", width=100, command=self.destroy
        ).pack(pady=(0, 16))


# ── Main customer view ────────────────────────────────────────────────────────
class CustomerView(ctk.CTkFrame):

    COLUMNS = [
        ("ID",        50),
        ("Name",     180),
        ("Phone",    130),
        ("Email",    190),
        ("Purchases", 90),
        ("Spent",    120),
        ("Actions",  200),
    ]

    def __init__(self, parent, current_user):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._svc  = CustomerService()
        self._user = current_user
        self._build_ui()
        self._load_customers()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text="Customers",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="＋  Add Customer",
            width=150,
            height=36,
            corner_radius=8,
            command=self._open_add_dialog,
        ).pack(side="right")

        # Search
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load_customers())

        ctk.CTkEntry(
            self,
            placeholder_text="🔍  Search by name, phone, or email…",
            textvariable=self._search_var,
            height=38,
            corner_radius=8,
        ).pack(fill="x", padx=24, pady=12)

        # Table
        wrap = ctk.CTkFrame(self, corner_radius=12)
        wrap.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        hdr = ctk.CTkFrame(
            wrap, fg_color=("gray80", "gray25"), corner_radius=8
        )
        hdr.pack(fill="x", padx=8, pady=(8, 0))

        for col, (label, width) in enumerate(self.COLUMNS):
            ctk.CTkLabel(
                hdr, text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width, anchor="w",
            ).grid(row=0, column=col,
                   padx=(10 if col == 0 else 4), pady=8, sticky="w")

        self._rows_frame = ctk.CTkScrollableFrame(
            wrap, fg_color="transparent", corner_radius=0
        )
        self._rows_frame.pack(fill="both", expand=True, padx=8, pady=4)

    def _load_customers(self):
        search = self._search_var.get() \
            if hasattr(self, "_search_var") else ""
        customers = self._svc.get_all(search)

        for w in self._rows_frame.winfo_children():
            w.destroy()

        if not customers:
            ctk.CTkLabel(
                self._rows_frame,
                text="No customers found.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, c in enumerate(customers):
            bg = ("gray92", "gray17") if i % 2 == 0 \
                else ("gray86", "gray20")
            row = ctk.CTkFrame(
                self._rows_frame, fg_color=bg,
                corner_radius=6, height=38
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            values = [
                (f"#{c.id}",                      50),
                (c.name,                          180),
                (c.phone  or "—",                 130),
                (c.email  or "—",                 190),
                (str(c.total_purchases),           90),
                (f"GH₵ {c.total_spent:,.2f}",     120),
            ]

            for col, (val, width) in enumerate(values):
                ctk.CTkLabel(
                    row, text=val,
                    font=ctk.CTkFont(size=12),
                    width=width, anchor="w",
                ).grid(row=0, column=col,
                       padx=(10 if col == 0 else 4),
                       pady=4, sticky="w")

            # Action buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=6, padx=4, pady=3, sticky="w")

            ctk.CTkButton(
                btn_frame,
                text="History",
                width=68,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "gray35"),
                hover_color=("gray65", "gray45"),
                text_color=("gray10", "gray90"),
                command=lambda cid=c.id: self._open_history(cid),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                btn_frame,
                text="Edit",
                width=58,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda cid=c.id: self._open_edit_dialog(cid),
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
                command=lambda cid=c.id,
                               cname=c.name: self._confirm_delete(cid, cname),
            ).pack(side="left")

    # ── Dialogs ───────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        CustomerFormDialog(self, on_save=self._save_new)

    def _open_edit_dialog(self, customer_id: int):
        customer = self._svc.get_by_id(customer_id)
        if customer:
            CustomerFormDialog(
                self,
                customer=customer,
                on_save=lambda n, p, e: self._save_edit(customer_id, n, p, e),
            )

    def _open_history(self, customer_id: int):
        customer = self._svc.get_by_id(customer_id)
        history  = self._svc.get_purchase_history(customer_id)
        if customer:
            PurchaseHistoryDialog(self, customer, history)

    def _save_new(self, name, phone, email):
        ok, msg = self._svc.create(name, phone, email)
        if ok:
            self._load_customers()

    def _save_edit(self, customer_id, name, phone, email):
        ok, msg = self._svc.update(customer_id, name, phone, email)
        if ok:
            self._load_customers()

    def _confirm_delete(self, customer_id: int, name: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Delete")
        dialog.geometry("360x180")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.lift()

        ctk.CTkLabel(
            dialog,
            text=f"Delete '{name}'?",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(28, 6))

        ctk.CTkLabel(
            dialog,
            text="Sales history will remain. This cannot be undone.",
            text_color="gray50",
            font=ctk.CTkFont(size=12),
            wraplength=300,
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
                self._svc.delete(customer_id),
                self._load_customers(),
                dialog.destroy(),
            ],
        ).pack(side="left", padx=8)