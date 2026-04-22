from database.connection import get_connection
from services.auth_service import AuthService


class UserService:

    # ── Read ──────────────────────────────────────────────────────────────────
    def get_all(self) -> list[dict]:
        conn = get_connection()
        rows = conn.execute("""
            SELECT  u.id,
                    u.username,
                    u.role,
                    u.created_at,
                    COUNT(s.id) AS total_sales
            FROM    users u
            LEFT JOIN sales s ON s.cashier_id = u.id
            GROUP BY u.id
            ORDER BY u.role, u.username
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_by_id(self, user_id: int) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT id, username, role, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    # ── Create ────────────────────────────────────────────────────────────────
    def create(self, username: str, password: str,
               role: str) -> tuple[bool, str]:
        if not username.strip():
            return False, "Username is required."
        if len(password) < 4:
            return False, "Password must be at least 4 characters."
        if role not in ("admin", "manager", "cashier"):
            return False, "Invalid role."

        ok = AuthService().create_user(username.strip(), password, role)
        if ok:
            return True, "User created successfully."
        return False, "Username already exists."

    # ── Update ────────────────────────────────────────────────────────────────
    def update(self, user_id: int, username: str,
               role: str) -> tuple[bool, str]:
        if not username.strip():
            return False, "Username is required."
        if role not in ("admin", "manager", "cashier"):
            return False, "Invalid role."
        try:
            conn = get_connection()
            conn.execute(
                "UPDATE users SET username = ?, role = ? WHERE id = ?",
                (username.strip(), role, user_id)
            )
            conn.commit()
            conn.close()
            return True, "User updated."
        except Exception as e:
            return False, str(e)

    def reset_password(self, user_id: int,
                       new_password: str) -> tuple[bool, str]:
        if len(new_password) < 4:
            return False, "Password must be at least 4 characters."
        try:
            AuthService().set_password(user_id, new_password)
            return True, "Password reset successfully."
        except Exception as e:
            return False, str(e)

    # ── Delete ────────────────────────────────────────────────────────────────
    def delete(self, user_id: int,
               current_user_id: int) -> tuple[bool, str]:
        if user_id == current_user_id:
            return False, "You cannot delete your own account."
        try:
            conn = get_connection()
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True, "User deleted."
        except Exception as e:
            return False, str(e)