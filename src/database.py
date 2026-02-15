"""
src/database.py
Local SQLite storage for credit accounts and transactions.
"""

import sqlite3
import os

DB_PATH = "credit_worthy.db"

def get_connection():
    """Returns a connection to the local database."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the database schema."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                credit_limit REAL NOT NULL,
                balance REAL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                amount REAL NOT NULL,
                type TEXT CHECK(type IN ('purchase', 'payment')),
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)
    print("Database initialized.")

def add_account(name, limit):
    """Adds a new credit account."""
    with get_connection() as conn:
        conn.execute("INSERT INTO accounts (name, credit_limit) VALUES (?, ?)", (name, limit))

def list_accounts():
    """Returns all accounts as a list of dictionaries."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM accounts")
        return [dict(row) for row in cursor.fetchall()]

def add_transaction(account_id, amount, tx_type):
    """Records a new transaction and updates the account balance."""
    with get_connection() as conn:
        conn.execute("INSERT INTO transactions (account_id, amount, type) VALUES (?, ?, ?)", 
                     (account_id, amount, tx_type))
        if tx_type == 'purchase':
            conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, account_id))
        else:
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, account_id))

if __name__ == "__main__":
    init_db()
    if not list_accounts():
        add_account("Main Credit Card", 5000)
    print("Current Accounts:", list_accounts())
