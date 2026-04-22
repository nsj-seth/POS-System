import customtkinter as ctk
from database.schema import initialise_database
from services.auth_service import AuthService
from ui.login_view import LoginView
from ui.dashboard_view import DashboardView
from ui.product_view import ProductView
from ui.sales_view import SalesView
from ui.payment_view import PaymentView
from ui.customer_view import CustomerView
from ui.receipt_view import ReceiptView
from ui.reports_view import ReportsView
from ui.user_view import UserView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    WIDTH  = 1100
    HEIGHT = 680

    def __init__(self):
        super().__init__()

        self.title("SwiftPOS")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(900, 600)

        self._current_user = None

        initialise_database()
        self._ensure_admin_password()
        self._show_login()

    # ── Ensure the seeded admin has a real bcrypt hash ────────────────────────
    def _ensure_admin_password(self):
        from database.connection import get_connection
        conn = get_connection()
        row  = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = 'admin'"
        ).fetchone()
        conn.close()

        if row and row["password_hash"] == "PLACEHOLDER":
            AuthService().set_password(row["id"], "admin123")
            print("[Auth] Admin password initialised.")

    # ── Views ─────────────────────────────────────────────────────────────────
    def _show_login(self):
        self._clear_window()
        login = LoginView(self, on_login_success=self._on_login)
        login.pack(fill="both", expand=True)

    def _on_login(self, user):
        self._current_user = user
        print(f"[Auth] Logged in as: {user.username} ({user.role})")
        self._show_main_app()

    def _show_main_app(self):
        self._clear_window()
        self._build_main_layout()
        self._on_dashboard()

    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ── Main layout ───────────────────────────────────────────────────────────
    def _build_main_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App name
        ctk.CTkLabel(
            self.sidebar,
            text="⚡ SwiftPOS",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(30, 4))

        # Logged-in user + role badge
        role_colors = {
            "admin":   ("#1a5276", "#2e86c1"),
            "manager": ("#145a32", "#1e8449"),
            "cashier": ("#4a235a", "#7d3c98"),
        }
        badge_color = role_colors.get(
            self._current_user.role, ("gray40", "gray60")
        )

        user_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=("gray85", "gray25"),
            corner_radius=8,
        )
        user_frame.pack(fill="x", padx=12, pady=(0, 16))

        ctk.CTkLabel(
            user_frame,
            text=self._current_user.username,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            user_frame,
            text=self._current_user.role.upper(),
            font=ctk.CTkFont(size=10),
            text_color=badge_color,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 8))

        # ── Nav items — only shown if user has permission ─────────────────────
        all_nav = [
            ("🏠  Dashboard",  "dashboard",  self._on_dashboard),
            ("🛍️  Sales",       "sales",      self._on_sales),
            ("📦  Products",    "products",   self._on_products),
            ("👥  Customers",   "customers",  self._on_customers),
            ("📊  Reports",     "reports",    self._on_reports),
            ("👤  Users",       "users",      self._on_users),
        ]

        for label, permission, command in all_nav:
            if self._current_user.can(permission):
                ctk.CTkButton(
                    self.sidebar,
                    text=label,
                    anchor="w",
                    height=42,
                    corner_radius=8,
                    fg_color="transparent",
                    hover_color=("gray70", "gray30"),
                    command=command,
                ).pack(fill="x", padx=12, pady=3)

        # Logout pinned to bottom
        ctk.CTkButton(
            self.sidebar,
            text="🚪  Logout",
            anchor="w",
            height=42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("#4a1515", "#4a1515"),
            text_color=("#c0392b", "#e05252"),
            command=self._logout,
        ).pack(side="bottom", fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        ).pack(side="bottom", pady=4)

        # Content area
        self.content = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.content.pack(side="left", fill="both", expand=True)

    # ── View loader ───────────────────────────────────────────────────────────
    def _load_view(self, view_class, *args, **kwargs):
        for w in self.content.winfo_children():
            w.destroy()
        view = view_class(self.content, *args, **kwargs)
        view.pack(fill="both", expand=True)

    # ── Permission guard ──────────────────────────────────────────────────────
    def _require_permission(self, permission: str) -> bool:
        """
        Returns True if allowed.
        Shows an access-denied screen and returns False if not.
        """
        if self._current_user.can(permission):
            return True

        for w in self.content.winfo_children():
            w.destroy()

        frame = ctk.CTkFrame(self.content, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame, text="🔒",
            font=ctk.CTkFont(size=48),
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            frame,
            text="Access Denied",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack()

        ctk.CTkLabel(
            frame,
            text=f"Your role  ({self._current_user.role})  does not have\n"
                 f"permission to access this section.",
            font=ctk.CTkFont(size=13),
            text_color="gray50",
            justify="center",
        ).pack(pady=(6, 0))

        return False

    # ── Nav handlers ──────────────────────────────────────────────────────────
    def _on_dashboard(self):
        if self._require_permission("dashboard"):
            self._load_view(DashboardView, self._current_user)

    def _on_sales(self):
        if self._require_permission("sales"):
            self._load_view(
                SalesView,
                self._current_user,
                on_checkout=self._on_checkout,
            )

    def _on_products(self):
        if self._require_permission("products"):
            self._load_view(ProductView, self._current_user)

    def _on_customers(self):
        if self._require_permission("customers"):
            self._load_view(CustomerView, self._current_user)

    def _on_reports(self):
        if self._require_permission("reports"):
            self._load_view(ReportsView, self._current_user)

    def _on_users(self):
        if self._require_permission("users"):
            self._load_view(UserView, self._current_user)

    # ── Checkout flow ─────────────────────────────────────────────────────────
    def _on_checkout(self, cart):
        for w in self.content.winfo_children():
            w.destroy()
        PaymentView(
            self.content,
            current_user=self._current_user,
            cart=cart,
            on_success=self._on_payment_success,
            on_back=self._on_sales,
        ).pack(fill="both", expand=True)

    def _on_payment_success(self, sale_id: int):
        for w in self.content.winfo_children():
            w.destroy()
        ReceiptView(
            self.content,
            current_user=self._current_user,
            sale_id=sale_id,
            on_new_sale=self._on_sales,
            on_dashboard=self._on_dashboard,
        ).pack(fill="both", expand=True)

    def _logout(self):
        self._current_user = None
        self._show_login()

    # ── Fallback content helper ───────────────────────────────────────────────
    def _set_content_text(self, title: str, subtitle: str = ""):
        for w in self.content.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.content,
            text=f"{title}\n\n{subtitle}",
            font=ctk.CTkFont(size=18),
            justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()