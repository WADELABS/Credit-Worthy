import sqlite3
import os

DB_PATH = 'database/credstack.db'

def get_db():
    """Get database connection"""
    if not os.path.exists('database'):
        os.makedirs('database')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database from setup scripts"""
    import subprocess
    if not os.path.exists(DB_PATH):
        subprocess.run(['python', 'setup.py'])
