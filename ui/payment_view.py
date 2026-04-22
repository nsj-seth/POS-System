import threading
import webbrowser
import customtkinter as ctk
from models.cart import Cart
from services.sales_service import SalesService
from services.paystack_service import PaystackService


MOMO_PROVIDERS = {
    "MTN Mobile Money":     "mtn",
    "Vodafone Cash":        "vodafone",
    "AirtelTigo Money":     "atl",
}


class PaymentView(ctk.CTkFrame):
    """Payment screen — cash, MoMo (Paystack), or Card (Paystack)."""

    METHODS = ["Cash", "Mobile Money", "Card"]

    def __init__(self, parent, current_user, cart: Cart,
                 on_success=None, on_back=None):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._user        = current_user
        self._cart        = cart
        self._svc         = SalesService()
        self._paystack    = PaystackService()
        self._on_success  = on_success
        self._on_back     = on_back
        self._reference   = ""      # active Paystack reference

        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════
    #  UI BUILD
    # ══════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 12))

        ctk.CTkButton(
            header, text="←  Back", width=90, height=32,
            corner_radius=8, fg_color="transparent", border_width=1,
            command=self._go_back,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="Payment",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left", padx=16)

        # Two-column body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_order_summary(body)
        self._build_payment_panel(body)

    # ── Left: order summary ───────────────────────────────────────────────
    def _build_order_summary(self, parent):
        panel = ctk.CTkFrame(parent, corner_radius=12)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            panel, text="Order Summary",
            font=ctk.CTkFont(size=15, weight="bold"), anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", corner_radius=0
        )
        scroll.pack(fill="both", expand=True, padx=8)

        for item in self._cart.items:
            row = ctk.CTkFrame(
                scroll, fg_color=("gray90", "gray20"), corner_radius=8
            )
            row.pack(fill="x", pady=2, padx=2)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            ctk.CTkLabel(
                left, text=item.product.name,
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                left,
                text=f"GH₵ {item.unit_price:,.2f}  ×  {item.quantity}",
                font=ctk.CTkFont(size=11), text_color="gray50", anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                row, text=f"GH₵ {item.subtotal:,.2f}",
                font=ctk.CTkFont(size=13), anchor="e",
            ).pack(side="right", padx=10)

        # Totals
        totals = ctk.CTkFrame(
            panel, fg_color=("gray85", "gray22"), corner_radius=10
        )
        totals.pack(fill="x", padx=10, pady=12)

        def summary_row(label, value, bold=False):
            r = ctk.CTkFrame(totals, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(
                r, text=label,
                font=ctk.CTkFont(
                    size=13, weight="bold" if bold else "normal"),
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                r, text=value,
                font=ctk.CTkFont(
                    size=13, weight="bold" if bold else "normal"),
                anchor="e",
            ).pack(side="right")

        summary_row("Subtotal",
                    f"GH₵ {self._cart.subtotal:,.2f}")
        summary_row("Discount",
                    f"− GH₵ {self._cart.discount_amount:,.2f}")
        summary_row("TOTAL",
                    f"GH₵ {self._cart.total:,.2f}", bold=True)

    # ── Right: payment panel ──────────────────────────────────────────────
    def _build_payment_panel(self, parent):
        self._pay_panel = ctk.CTkFrame(parent, corner_radius=12)
        self._pay_panel.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(
            self._pay_panel, text="Payment Details",
            font=ctk.CTkFont(size=15, weight="bold"), anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 12))

        form = ctk.CTkFrame(self._pay_panel, fg_color="transparent")
        form.pack(fill="x", padx=16)

        # Payment method selector
        ctk.CTkLabel(form, text="Payment Method", anchor="w").pack(
            fill="x", pady=(0, 6)
        )
        self._method_var = ctk.StringVar(value="Cash")
        method_frame = ctk.CTkFrame(form, fg_color="transparent")
        method_frame.pack(fill="x", pady=(0, 14))

        for method in self.METHODS:
            ctk.CTkRadioButton(
                method_frame, text=method,
                variable=self._method_var, value=method,
                command=self._on_method_change,
            ).pack(side="left", padx=(0, 16))

        # ── Cash fields ───────────────────────────────────────────────────
        self._cash_frame = ctk.CTkFrame(form, fg_color="transparent")
        self._cash_frame.pack(fill="x")

        ctk.CTkLabel(
            self._cash_frame,
            text="Amount Paid (GH₵)", anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self._amount_entry = ctk.CTkEntry(
            self._cash_frame,
            placeholder_text=f"{self._cart.total:,.2f}",
            height=42, corner_radius=8,
            font=ctk.CTkFont(size=16),
        )
        self._amount_entry.pack(fill="x")
        self._amount_entry.bind(
            "<KeyRelease>", self._on_amount_change
        )

        # Quick-fill buttons
        quick_frame = ctk.CTkFrame(
            self._cash_frame, fg_color="transparent"
        )
        quick_frame.pack(fill="x", pady=(6, 0))

        for amt in self._get_quick_amounts(self._cart.total):
            ctk.CTkButton(
                quick_frame,
                text=f"GH₵ {amt:,.0f}", height=30, width=72,
                corner_radius=6, font=ctk.CTkFont(size=11),
                fg_color=("gray80", "gray30"),
                hover_color=("gray70", "gray40"),
                text_color=("gray10", "gray90"),
                command=lambda a=amt: self._quick_fill(a),
            ).pack(side="left", padx=(0, 6))

        # Change display (cash only)
        self._change_box = ctk.CTkFrame(
            self._pay_panel,
            fg_color=("gray85", "gray22"), corner_radius=10,
        )
        self._change_box.pack(fill="x", padx=16, pady=12)

        change_inner = ctk.CTkFrame(
            self._change_box, fg_color="transparent"
        )
        change_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            change_inner, text="Change Due",
            font=ctk.CTkFont(size=13), anchor="w",
        ).pack(side="left")

        self._change_lbl = ctk.CTkLabel(
            change_inner, text="GH₵ 0.00",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1a7abf", "#4da6e8"), anchor="e",
        )
        self._change_lbl.pack(side="right")

        # ── MoMo fields ───────────────────────────────────────────────────
        self._momo_frame = ctk.CTkFrame(form, fg_color="transparent")

        ctk.CTkLabel(
            self._momo_frame,
            text="Mobile Money Provider", anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self._provider_var = ctk.StringVar(
            value="MTN Mobile Money"
        )
        ctk.CTkOptionMenu(
            self._momo_frame,
            values=list(MOMO_PROVIDERS.keys()),
            variable=self._provider_var,
            height=38, corner_radius=8,
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            self._momo_frame,
            text="Customer Phone Number", anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self._momo_phone = ctk.CTkEntry(
            self._momo_frame,
            placeholder_text="e.g. 0241234567",
            height=38, corner_radius=8,
        )
        self._momo_phone.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            self._momo_frame,
            text="Customer Email (optional)", anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self._momo_email = ctk.CTkEntry(
            self._momo_frame,
            placeholder_text="customer@email.com",
            height=38, corner_radius=8,
        )
        self._momo_email.pack(fill="x")

        # OTP frame (shown only for Vodafone)
        self._otp_frame = ctk.CTkFrame(
            self._momo_frame, fg_color="transparent"
        )
        ctk.CTkLabel(
            self._otp_frame,
            text="Enter OTP (sent to customer)", anchor="w"
        ).pack(fill="x", pady=(10, 4))

        self._otp_entry = ctk.CTkEntry(
            self._otp_frame,
            placeholder_text="6-digit OTP",
            height=38, corner_radius=8,
        )
        self._otp_entry.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(
            self._otp_frame,
            text="Submit OTP",
            height=36, corner_radius=8,
            command=self._submit_otp,
        ).pack(fill="x")

        # ── Card fields ───────────────────────────────────────────────────
        self._card_frame = ctk.CTkFrame(form, fg_color="transparent")

        ctk.CTkLabel(
            self._card_frame,
            text="Customer Email *", anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self._card_email = ctk.CTkEntry(
            self._card_frame,
            placeholder_text="customer@email.com",
            height=38, corner_radius=8,
        )
        self._card_email.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            self._card_frame,
            text=(
                "A secure Paystack payment page will open in the\n"
                "browser. Customer completes payment there."
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray50",
            justify="left",
            anchor="w",
        ).pack(fill="x")

        # ── Status / progress label ───────────────────────────────────────
        self._status_frame = ctk.CTkFrame(
            self._pay_panel,
            fg_color=("gray85", "gray22"), corner_radius=10,
        )
        self._status_lbl = ctk.CTkLabel(
            self._status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            wraplength=260,
            justify="center",
        )
        self._status_lbl.pack(padx=14, pady=12)

        # ── Error label ───────────────────────────────────────────────────
        self._error_lbl = ctk.CTkLabel(
            self._pay_panel, text="",
            text_color="#e05252",
            font=ctk.CTkFont(size=12), wraplength=280,
        )
        self._error_lbl.pack(padx=16, pady=(4, 0))

        # ── Confirm button ────────────────────────────────────────────────
        self._confirm_btn = ctk.CTkButton(
            self._pay_panel,
            text="✓  Confirm Payment",
            height=50, corner_radius=10,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#1e8449", hover_color="#145a32",
            command=self._confirm_payment,
        )
        self._confirm_btn.pack(fill="x", padx=16, pady=(8, 20))

    # ══════════════════════════════════════════════════════════════════════
    #  METHOD SWITCHING
    # ══════════════════════════════════════════════════════════════════════
    def _on_method_change(self):
        method = self._method_var.get()

        # Hide all conditional frames
        self._cash_frame.pack_forget()
        self._change_box.pack_forget()
        self._momo_frame.pack_forget()
        self._card_frame.pack_forget()
        self._status_frame.pack_forget()
        self._otp_frame.pack_forget()
        self._error_lbl.configure(text="")

        form = self._cash_frame.master

        if method == "Cash":
            self._cash_frame.pack(fill="x", in_=form)
            self._change_box.pack(
                fill="x", padx=16, pady=12,
                before=self._error_lbl,
            )
            self._confirm_btn.configure(
                text="✓  Confirm Payment", state="normal"
            )

        elif method == "Mobile Money":
            self._momo_frame.pack(fill="x", in_=form)
            self._status_frame.pack(
                fill="x", padx=16, pady=(8, 4),
                before=self._error_lbl,
            )
            self._confirm_btn.configure(
                text="📱  Send MoMo Request", state="normal"
            )

        elif method == "Card":
            self._card_frame.pack(fill="x", in_=form)
            self._status_frame.pack(
                fill="x", padx=16, pady=(8, 4),
                before=self._error_lbl,
            )
            self._confirm_btn.configure(
                text="💳  Open Card Payment", state="normal"
            )

    # ══════════════════════════════════════════════════════════════════════
    #  CASH HELPERS
    # ══════════════════════════════════════════════════════════════════════
    def _get_quick_amounts(self, total: float) -> list:
        import math
        rounded = math.ceil(total / 10) * 10
        amounts = sorted({
            rounded, rounded + 10, rounded + 20, rounded + 50
        })
        return amounts[:4]

    def _quick_fill(self, amount: float):
        self._amount_entry.delete(0, "end")
        self._amount_entry.insert(0, f"{amount:.2f}")
        self._on_amount_change()

    def _on_amount_change(self, _event=None):
        try:
            paid   = float(self._amount_entry.get())
            change = round(paid - self._cart.total, 2)
            if change >= 0:
                self._change_lbl.configure(
                    text=f"GH₵ {change:,.2f}",
                    text_color=("#1a7abf", "#4da6e8"),
                )
            else:
                self._change_lbl.configure(
                    text=f"− GH₵ {abs(change):,.2f}",
                    text_color=("#c0392b", "#e05252"),
                )
        except ValueError:
            self._change_lbl.configure(text="GH₵ 0.00")

    # ══════════════════════════════════════════════════════════════════════
    #  CONFIRM PAYMENT — dispatcher
    # ══════════════════════════════════════════════════════════════════════
    def _confirm_payment(self):
        self._error_lbl.configure(text="")
        method = self._method_var.get()

        if method == "Cash":
            self._process_cash()
        elif method == "Mobile Money":
            self._process_momo()
        elif method == "Card":
            self._process_card()

    # ══════════════════════════════════════════════════════════════════════
    #  CASH
    # ══════════════════════════════════════════════════════════════════════
    def _process_cash(self):
        try:
            amount_paid = float(self._amount_entry.get())
        except ValueError:
            self._error_lbl.configure(
                text="Please enter the amount paid."
            )
            return

        if amount_paid < self._cart.total:
            self._error_lbl.configure(
                text=f"Amount paid is less than total "
                     f"(GH₵ {self._cart.total:,.2f})."
            )
            return

        self._confirm_btn.configure(
            state="disabled", text="Processing…"
        )
        ok, msg, sale_id = self._svc.process_sale(
            cart=self._cart,
            payment_method="cash",
            amount_paid=amount_paid,
            cashier_id=self._user.id,
        )
        if ok:
            self._on_success(sale_id)
        else:
            self._error_lbl.configure(text=f"Error: {msg}")
            self._confirm_btn.configure(
                state="normal", text="✓  Confirm Payment"
            )

    # ══════════════════════════════════════════════════════════════════════
    #  MOBILE MONEY
    # ══════════════════════════════════════════════════════════════════════
    def _process_momo(self):
        phone    = self._momo_phone.get().strip()
        email    = self._momo_email.get().strip() or \
                   "customer@swiftpos.com"
        provider = MOMO_PROVIDERS[self._provider_var.get()]

        if not phone:
            self._error_lbl.configure(
                text="Please enter the customer's phone number."
            )
            return

        self._set_processing("Sending MoMo request…")

        def run():
            ok, msg, ref = self._paystack.charge_momo(
                amount_ghs=self._cart.total,
                phone=phone,
                provider=provider,
                email=email,
            )
            if not ok:
                self.after(0, lambda: self._set_error(msg))
                return

            self._reference = ref

            # Vodafone needs OTP
            if provider == "vodafone":
                self.after(0, self._show_otp_entry)
                return

            # MTN / AirtelTigo — poll for approval
            self.after(0, lambda: self._set_status(
                "⏳ Waiting for customer to approve on their phone…\n"
                "This may take up to 2 minutes."
            ))

            success, status = self._paystack.poll_until_success(
                reference=ref,
                on_attempt=lambda a, m: self.after(
                    0, lambda: self._set_status(
                        f"⏳ Waiting for approval…  "
                        f"({a * 5}s / {m * 5}s)"
                    )
                ),
            )

            if success:
                self.after(0, self._finalize_paystack_sale)
            else:
                self.after(0, lambda s=status: self._set_error(
                    f"Payment {s}. Please try again."
                ))

        threading.Thread(target=run, daemon=True).start()

    def _show_otp_entry(self):
        """Show OTP field for Vodafone Cash."""
        self._otp_frame.pack(fill="x", pady=(10, 0))
        self._set_status(
            "📱 OTP sent to customer's phone.\n"
            "Enter the OTP below to complete payment."
        )
        self._confirm_btn.configure(
            state="normal", text="📱  Send MoMo Request"
        )

    def _submit_otp(self):
        otp = self._otp_entry.get().strip()
        if not otp:
            self._error_lbl.configure(text="Please enter the OTP.")
            return

        self._set_processing("Submitting OTP…")

        def run():
            ok, msg = self._paystack.submit_otp(
                otp=otp, reference=self._reference
            )
            if not ok:
                self.after(0, lambda: self._set_error(msg))
                return

            success, status = self._paystack.poll_until_success(
                reference=self._reference,
            )
            if success:
                self.after(0, self._finalize_paystack_sale)
            else:
                self.after(0, lambda s=status: self._set_error(
                    f"Payment {s}. Please try again."
                ))

        threading.Thread(target=run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════
    #  CARD
    # ══════════════════════════════════════════════════════════════════════
    def _process_card(self):
        email = self._card_email.get().strip() or \
                "customer@swiftpos.com"

        self._set_processing("Initializing card payment…")

        def run():
            ok, url_or_msg, ref = \
                self._paystack.initialize_card_payment(
                    amount_ghs=self._cart.total,
                    email=email,
                )
            if not ok:
                self.after(0, lambda: self._set_error(url_or_msg))
                return

            self._reference = ref

            # Open payment link in browser
            webbrowser.open(url_or_msg)

            self.after(0, lambda: self._set_status(
                "💳 Payment page opened in browser.\n"
                "Waiting for customer to complete payment…"
            ))

            # Poll for completion
            success, status = self._paystack.poll_until_success(
                reference=ref,
                on_attempt=lambda a, m: self.after(
                    0, lambda: self._set_status(
                        f"💳 Waiting for card payment…  "
                        f"({a * 5}s / {m * 5}s)"
                    )
                ),
            )

            if success:
                self.after(0, self._finalize_paystack_sale)
            else:
                self.after(0, lambda s=status: self._set_error(
                    f"Payment {s}. Please try again."
                ))

        threading.Thread(target=run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════
    #  FINALIZE — save sale after Paystack confirms
    # ══════════════════════════════════════════════════════════════════════
    def _finalize_paystack_sale(self):
        method = self._method_var.get().lower().replace(" ", "_")

        ok, msg, sale_id = self._svc.process_sale(
            cart=self._cart,
            payment_method=method,
            amount_paid=self._cart.total,
            cashier_id=self._user.id,
        )
        if ok:
            self._on_success(sale_id)
        else:
            self._set_error(f"Sale save error: {msg}")

    # ══════════════════════════════════════════════════════════════════════
    #  UI STATE HELPERS
    # ══════════════════════════════════════════════════════════════════════
    def _set_processing(self, msg: str):
        self._error_lbl.configure(text="")
        self._confirm_btn.configure(state="disabled", text="Please wait…")
        self._set_status(msg)

    def _set_status(self, msg: str):
        self._status_frame.pack(
            fill="x", padx=16, pady=(8, 4),
            before=self._error_lbl,
        )
        self._status_lbl.configure(text=msg)

    def _set_error(self, msg: str):
        self._error_lbl.configure(text=msg)
        self._status_lbl.configure(text="")
        method = self._method_var.get()
        labels = {
            "Cash":         "✓  Confirm Payment",
            "Mobile Money": "📱  Send MoMo Request",
            "Card":         "💳  Open Card Payment",
        }
        self._confirm_btn.configure(
            state="normal", text=labels.get(method, "Confirm")
        )

    def _go_back(self):
        if self._on_back:
            self._on_back()