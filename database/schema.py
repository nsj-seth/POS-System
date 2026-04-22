from database.connection import get_connection


def initialise_database():
    """Create all tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Users (authentication) ────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL CHECK(role IN ('admin', 'manager', 'cashier')),
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Categories ────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        )
    """)

    # ── Products ──────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            category_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            price         REAL    NOT NULL CHECK(price >= 0),
            quantity      INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            barcode       TEXT    UNIQUE,
            low_stock_qty INTEGER NOT NULL DEFAULT 5,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Customers ─────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            phone      TEXT,
            email      TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Sales (one row per transaction) ───────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id     INTEGER REFERENCES customers(id) ON DELETE SET NULL,
            cashier_id      INTEGER REFERENCES users(id)     ON DELETE SET NULL,
            total_amount    REAL NOT NULL,
            discount_amount REAL NOT NULL DEFAULT 0,
            payment_method  TEXT NOT NULL CHECK(payment_method IN ('cash', 'mobile_money', 'card')),
            amount_paid     REAL NOT NULL,
            change_given    REAL NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Sale items (one row per product line in a sale) ───────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id    INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
            quantity   INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL    NOT NULL,
            subtotal   REAL    NOT NULL
        )
    """)

    # ── Seed a default admin user if none exists ──────────────────────────────
    existing = cursor.execute(
        "SELECT id FROM users WHERE username = 'admin'"
    ).fetchone()

    if not existing:
        import bcrypt
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", hashed, "admin")
        )

    # ── Seed some starter categories ──────────────────────────────────────────
    for category in ["Food & Drinks", "Electronics", "Clothing", "General"]:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)", (category,)
        )

    conn.commit()
    conn.close()
    print("[DB] Database initialised successfully.")


if __name__ == "__main__":
    initialise_database()