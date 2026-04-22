import bcrypt
from models.user import User
from database.connection import get_connection


class AuthService:
    """Handles user authentication and password management."""

    # ── Login ─────────────────────────────────────────────────────────────────
    def login(self, username: str, password: str) -> User | None:
        """
        Verify credentials. Returns a User on success, None on failure.
        """
        conn = get_connection()
        row = conn.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username.strip(),)
        ).fetchone()
        conn.close()

        if row is None:
            return None

        # Compare supplied password against stored hash
        password_bytes = password.encode("utf-8")
        stored_hash    = row["password_hash"].encode("utf-8")

        try:
            if bcrypt.checkpw(password_bytes, stored_hash):
                return User(id=row["id"], username=row["username"], role=row["role"])
        except Exception:
            pass

        return None

    # ── Seed / reset admin password ───────────────────────────────────────────
    def set_password(self, user_id: int, plain_password: str) -> None:
        """Hash and store a new password for a user."""
        hashed = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        conn = get_connection()
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hashed, user_id)
        )
        conn.commit()
        conn.close()

    # ── Create user ───────────────────────────────────────────────────────────
    def create_user(self, username: str, plain_password: str, role: str) -> bool:
        """Create a new user. Returns True on success, False if username exists."""
        hashed = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username.strip(), hashed, role)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False