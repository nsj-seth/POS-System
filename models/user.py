from dataclasses import dataclass


# ── Permission sets per role ───────────────────────────────────────────────────
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "dashboard", "sales", "products",
        "customers", "reports", "users",
    },
    "manager": {
        "dashboard", "sales", "products",
        "customers", "reports",
    },
    "cashier": {
        "dashboard", "sales",
    },
}


@dataclass
class User:
    """Represents an authenticated user session."""
    id:       int
    username: str
    role:     str          # 'admin' | 'manager' | 'cashier'

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role in ("admin", "manager")

    def can(self, permission: str) -> bool:
        """Check if this user has a specific permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, set())