import os
import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "expense_tracker.db")

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

# werkzeug's default (scrypt) needs hashlib.scrypt, which is missing when Python
# is built against LibreSSL (e.g. macOS Command Line Tools Python 3.9).
# pbkdf2:sha256 works everywhere; reuse this constant wherever passwords are hashed.
PASSWORD_HASH_METHOD = "pbkdf2:sha256"

# Used only when SPENDLY_DEMO_PASSWORD is unset AND the app runs in dev mode.
_DEV_DEMO_PASSWORD = "demo123"


def get_db():
    """Return a SQLite connection with dict-like rows and foreign keys enforced."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables. Safe to call multiple times."""
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,
                description TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db(dev_mode=False):
    """Insert a demo user and sample expenses, only if the users table is empty."""
    conn = get_db()
    try:
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count > 0:
            return

        password = os.environ.get("SPENDLY_DEMO_PASSWORD")
        if not password:
            if not dev_mode:
                print("seed_db: SPENDLY_DEMO_PASSWORD not set outside dev mode; skipping seed.")
                return
            password = _DEV_DEMO_PASSWORD

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash(password, method=PASSWORD_HASH_METHOD)),
        )
        user_id = cursor.lastrowid

        today = date.today()

        def day(d):
            return today.replace(day=min(d, today.day)).isoformat()

        expenses = [
            (user_id, 450.00, "Food", day(1), "Groceries"),
            (user_id, 120.00, "Transport", day(3), "Metro card top-up"),
            (user_id, 1850.00, "Bills", day(5), "Electricity bill"),
            (user_id, 600.00, "Health", day(7), "Pharmacy"),
            (user_id, 499.00, "Entertainment", day(9), "Movie tickets"),
            (user_id, 2299.00, "Shopping", day(11), "Shoes"),
            (user_id, 300.00, "Other", day(13), "Gift wrap"),
            (user_id, 780.00, "Food", day(15), "Dinner out"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            expenses,
        )
        conn.commit()
    finally:
        conn.close()
