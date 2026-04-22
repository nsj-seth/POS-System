import customtkinter as ctk
from services.user_service import UserService


ROLES = ["admin", "manager", "cashier"]

ROLE_COLORS = {
    "admin":   ("#1a5276", "#2e86c1"),
    "manager": ("#145a32", "#1e8449"),
    "cashier": ("#4a235a", "#7d3c98"),
}


# ── Create / Edit dialog ──────────────────────────────────────────────────────
class UserFormDialog(ctk.CTkToplevel):

    def __init__(self, parent, user=None, on_save=None):
        super().__init__(parent)
        self._user    = user
        self._on_save = on_save
        self._is_edit = user is not None

        self.title("Edit User" if self._is_edit else "Add User")
        self.geometry("420x440")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self._build_ui()
        if self._is_edit:
            self._populate()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Edit User" if self._is_edit else "Add New User",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 16))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=28)

        # Username
        ctk.CTkLabel(form, text="Username *", anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._username_entry = ctk.CTkEntry(
            form, placeholder_text="e.g. john_doe",
            height=38, corner_radius=8
        )
        self._username_entry.pack(fill="x", pady=(0, 14))

        # Role
        ctk.CTkLabel(form, text="Role *", anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._role_var = ctk.StringVar(value="cashier")
        role_frame = ctk.CTkFrame(form, fg_color="transparent")
        role_frame.pack(fill="x", pady=(0, 14))

        for role in ROLES:
            ctk.CTkRadioButton(
                role_frame,
                text=role.capitalize(),
                variable=self._role_var,
                value=role,
            ).pack(side="left", padx=(0, 20))

        # Password (only for new users)
        if not self._is_edit:
            ctk.CTkLabel(form, text="Password *", anchor="w").pack(
                fill="x", pady=(0, 4)
            )
            self._password_entry = ctk.CTkEntry(
                form, placeholder_text="Min. 4 characters",
                show="•", height=38, corner_radius=8
            )
            self._password_entry.pack(fill="x", pady=(0, 4))

            ctk.CTkLabel(
                form,
                text="User will be asked to change password on first login.",
                font=ctk.CTkFont(size=11),
                text_color="gray50",
                anchor="w",
            ).pack(fill="x")

        # Error
        self._error = ctk.CTkLabel(
            self, text="", text_color="#e05252",
            font=ctk.CTkFont(size=12)
        )
        self._error.pack(pady=(12, 0))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(8, 24))

        ctk.CTkButton(
            btn_row, text="Cancel", width=110, height=40,
            fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Save User", width=140, height=40,
            command=self._submit,
        ).pack(side="right")

    def _populate(self):
        self._username_entry.insert(0, self._user["username"])
        self._role_var.set(self._user["role"])

    def _submit(self):
        username = self._username_entry.get().strip()
        role     = self._role_var.get()

        if not username:
            self._error.configure(text="Username is required.")
            return

        if not self._is_edit:
            password = self._password_entry.get()
            if len(password) < 4:
                self._error.configure(
                    text="Password must be at least 4 characters."
                )
                return
            if self._on_save:
                self._on_save(username, role, password)
        else:
            if self._on_save:
                self._on_save(username, role)

        self.destroy()


# ── Reset password dialog ─────────────────────────────────────────────────────
class ResetPasswordDialog(ctk.CTkToplevel):

    def __init__(self, parent, user: dict, on_reset=None):
        super().__init__(parent)
        self._user     = user
        self._on_reset = on_reset

        self.title("Reset Password")
        self.geometry("380x300")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="Reset Password",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text=f"User: {self._user['username']}",
            font=ctk.CTkFont(size=12),
            text_color="gray50",
        ).pack(pady=(0, 20))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=28)

        ctk.CTkLabel(form, text="New Password *", anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._new_pass = ctk.CTkEntry(
            form, placeholder_text="Min. 4 characters",
            show="•", height=38, corner_radius=8
        )
        self._new_pass.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Confirm Password *", anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self._confirm_pass = ctk.CTkEntry(
            form, placeholder_text="Repeat password",
            show="•", height=38, corner_radius=8
        )
        self._confirm_pass.pack(fill="x")

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
            btn_row, text="Reset Password", width=150, height=40,
            fg_color="#1e8449", hover_color="#145a32",
            command=self._submit,
        ).pack(side="right")

    def _submit(self):
        new  = self._new_pass.get()
        conf = self._confirm_pass.get()

        if len(new) < 4:
            self._error.configure(
                text="Password must be at least 4 characters."
            )
            return
        if new != conf:
            self._error.configure(text="Passwords do not match.")
            return

        if self._on_reset:
            self._on_reset(new)
        self.destroy()


# ── Main user management view ─────────────────────────────────────────────────
class UserView(ctk.CTkFrame):

    COLUMNS = [
        ("ID",         50),
        ("Username",  180),
        ("Role",      110),
        ("Sales",      80),
        ("Created",   160),
        ("Actions",   220),
    ]

    def __init__(self, parent, current_user):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self._svc          = UserService()
        self._current_user = current_user
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 0))

        ctk.CTkLabel(
            header,
            text="User Management",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="＋  Add User",
            width=130,
            height=36,
            corner_radius=8,
            command=self._open_add_dialog,
        ).pack(side="right")

        # Info banner
        ctk.CTkLabel(
            self,
            text="🔒  Only administrators can access this screen.",
            font=ctk.CTkFont(size=12),
            text_color="gray50",
            anchor="w",
        ).pack(fill="x", padx=24, pady=(8, 4))

        # Table
        wrap = ctk.CTkFrame(self, corner_radius=12)
        wrap.pack(fill="both", expand=True, padx=24, pady=(8, 24))

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
                   padx=(10 if col == 0 else 4),
                   pady=8, sticky="w")

        self._rows_frame = ctk.CTkScrollableFrame(
            wrap, fg_color="transparent", corner_radius=0
        )
        self._rows_frame.pack(fill="both", expand=True, padx=8, pady=4)

    def _load_users(self):
        users = self._svc.get_all()

        for w in self._rows_frame.winfo_children():
            w.destroy()

        if not users:
            ctk.CTkLabel(
                self._rows_frame,
                text="No users found.",
                text_color="gray50",
            ).pack(pady=20)
            return

        for i, u in enumerate(users):
            is_self = u["id"] == self._current_user.id
            bg = ("gray92", "gray17") if i % 2 == 0 \
                else ("gray86", "gray20")

            row = ctk.CTkFrame(
                self._rows_frame, fg_color=bg,
                corner_radius=6, height=40,
            )
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            # Date formatting
            created = u["created_at"][:10] if u["created_at"] else "—"

            # Role badge color
            role_color = ROLE_COLORS.get(
                u["role"], ("gray40", "gray60")
            )

            values = [
                (f"#{u['id']}",          50,  None),
                (u["username"] +
                 (" (you)" if is_self else ""),
                                         180,  None),
                (u["role"].upper(),      110,  role_color),
                (str(u["total_sales"]),   80,  None),
                (created,               160,  None),
            ]

            for col, (val, width, color) in enumerate(values):
                lbl = ctk.CTkLabel(
                    row, text=val,
                    font=ctk.CTkFont(size=12),
                    width=width, anchor="w",
                )
                if color:
                    lbl.configure(text_color=color)
                lbl.grid(row=0, column=col,
                         padx=(10 if col == 0 else 4),
                         pady=4, sticky="w")

            # Action buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=5, padx=4, pady=4, sticky="w")

            ctk.CTkButton(
                btn_frame,
                text="Edit",
                width=58, height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda uid=u["id"]: self._open_edit_dialog(uid),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(
                btn_frame,
                text="Password",
                width=78, height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "gray35"),
                hover_color=("gray65", "gray45"),
                text_color=("gray10", "gray90"),
                command=lambda uid=u["id"]: self._open_reset_dialog(uid),
            ).pack(side="left", padx=(0, 4))

            delete_btn = ctk.CTkButton(
                btn_frame,
                text="Delete",
                width=62, height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color="#c0392b",
                hover_color="#922b21",
                state="disabled" if is_self else "normal",
                command=lambda uid=u["id"],
                               uname=u["username"]: self._confirm_delete(
                                   uid, uname
                               ),
            )
            delete_btn.pack(side="left")

    # ── Dialogs ───────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        UserFormDialog(
            self,
            on_save=lambda username, role, password:
                self._save_new(username, role, password),
        )

    def _open_edit_dialog(self, user_id: int):
        user = self._svc.get_by_id(user_id)
        if user:
            UserFormDialog(
                self,
                user=user,
                on_save=lambda username, role:
                    self._save_edit(user_id, username, role),
            )

    def _open_reset_dialog(self, user_id: int):
        user = self._svc.get_by_id(user_id)
        if user:
            ResetPasswordDialog(
                self,
                user=user,
                on_reset=lambda new_pass:
                    self._do_reset(user_id, new_pass),
            )

    def _save_new(self, username: str, role: str, password: str):
        ok, msg = self._svc.create(username, password, role)
        if ok:
            self._load_users()
        else:
            self._show_error(msg)

    def _save_edit(self, user_id: int, username: str, role: str):
        ok, msg = self._svc.update(user_id, username, role)
        if ok:
            self._load_users()
        else:
            self._show_error(msg)

    def _do_reset(self, user_id: int, new_password: str):
        ok, msg = self._svc.reset_password(user_id, new_password)
        if not ok:
            self._show_error(msg)
        else:
            self._show_success(msg)

    def _confirm_delete(self, user_id: int, username: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Delete")
        dialog.geometry("360x190")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.lift()

        ctk.CTkLabel(
            dialog,
            text=f"Delete user '{username}'?",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(28, 6))

        ctk.CTkLabel(
            dialog,
            text="Their sales history will remain.\nThis cannot be undone.",
            text_color="gray50",
            font=ctk.CTkFont(size=12),
            justify="center",
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
            command=lambda: self._do_delete(user_id, dialog),
        ).pack(side="left", padx=8)

    def _do_delete(self, user_id: int, dialog):
        ok, msg = self._svc.delete(user_id, self._current_user.id)
        dialog.destroy()
        if ok:
            self._load_users()
        else:
            self._show_error(msg)

    # ── Feedback helpers ──────────────────────────────────────────────────────
    def _show_error(self, message: str):
        self._show_toast(message, error=True)

    def _show_success(self, message: str):
        self._show_toast(message, error=False)

    def _show_toast(self, message: str, error: bool = False):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        color = ("#c0392b", "#922b21") if error else ("#1e8449", "#145a32")
        ctk.CTkLabel(
            toast, text=message,
            font=ctk.CTkFont(size=12),
            fg_color=color,
            corner_radius=8,
            padx=16, pady=10,
        ).pack()

        x = self.winfo_rootx() + self.winfo_width() - 360
        y = self.winfo_rooty() + 60
        toast.geometry(f"+{x}+{y}")
        toast.after(2500, toast.destroy)