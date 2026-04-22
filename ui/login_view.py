import customtkinter as ctk
from services.auth_service import AuthService


class LoginView(ctk.CTkFrame):
    """Full-screen login form."""

    def __init__(self, parent, on_login_success):
        """
        parent           – the root App window
        on_login_success – callback(user: User) called after valid login
        """
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._auth    = AuthService()
        self._on_success = on_login_success

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Centre card
        card = ctk.CTkFrame(self, width=400, height=480, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        # Logo / title
        ctk.CTkLabel(
            card,
            text="⚡ SwiftPOS",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(40, 4))

        ctk.CTkLabel(
            card,
            text="Sign in to continue",
            font=ctk.CTkFont(size=13),
            text_color="gray60",
        ).pack(pady=(0, 30))

        # Username
        ctk.CTkLabel(card, text="Username", anchor="w").pack(
            fill="x", padx=40
        )
        self._username_entry = ctk.CTkEntry(
            card, placeholder_text="Enter username", height=42, corner_radius=8
        )
        self._username_entry.pack(fill="x", padx=40, pady=(4, 14))

        # Password
        ctk.CTkLabel(card, text="Password", anchor="w").pack(
            fill="x", padx=40
        )
        self._password_entry = ctk.CTkEntry(
            card,
            placeholder_text="Enter password",
            show="•",
            height=42,
            corner_radius=8,
        )
        self._password_entry.pack(fill="x", padx=40, pady=(4, 6))

        # Error label (hidden until needed)
        self._error_label = ctk.CTkLabel(
            card, text="", text_color="#e05252", font=ctk.CTkFont(size=12)
        )
        self._error_label.pack(pady=(0, 10))

        # Login button
        self._login_btn = ctk.CTkButton(
            card,
            text="Sign In",
            height=44,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._attempt_login,
        )
        self._login_btn.pack(fill="x", padx=40, pady=(4, 0))

        # Hint
        ctk.CTkLabel(
            card,
            text="Default: admin / admin123",
            font=ctk.CTkFont(size=11),
            text_color="gray50",
        ).pack(pady=(12, 0))

        # Allow pressing Enter to submit
        self._password_entry.bind("<Return>", lambda _: self._attempt_login())
        self._username_entry.bind("<Return>", lambda _: self._attempt_login())

    # ── Login logic ───────────────────────────────────────────────────────────
    def _attempt_login(self):
        username = self._username_entry.get().strip()
        password = self._password_entry.get()

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        self._login_btn.configure(state="disabled", text="Signing in…")
        self.after(100, lambda: self._do_login(username, password))

    def _do_login(self, username: str, password: str):
        user = self._auth.login(username, password)

        if user:
            self._show_error("")
            self._on_success(user)
        else:
            self._show_error("Invalid username or password.")
            self._login_btn.configure(state="normal", text="Sign In")

    def _show_error(self, message: str):
        self._error_label.configure(text=message)