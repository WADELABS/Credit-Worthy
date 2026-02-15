#!/usr/bin/env python3
"""
Migration: Add password and authentication fields to users table
"""

import sqlite3
import sys

def upgrade(db_path='database/credstack.db'):
    """Add password and auth-related fields"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add password_hash field
        cursor.execute('''
            ALTER TABLE users ADD COLUMN password_hash TEXT
        ''')
        
        # Add account lockout fields
        cursor.execute('''
            ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0
        ''')
        
        cursor.execute('''
            ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMP
        ''')
        
        # Add last login tracking
        cursor.execute('''
            ALTER TABLE users ADD COLUMN last_login TIMESTAMP
        ''')
        
        # Add API token field
        cursor.execute('''
            ALTER TABLE users ADD COLUMN api_token TEXT
        ''')
        
        cursor.execute('''
            ALTER TABLE users ADD COLUMN api_token_created TIMESTAMP
        ''')
        
        conn.commit()
        print("✓ Migration 001_add_password_fields applied successfully")
        return True
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠ Migration already applied")
            return True
        else:
            print(f"✗ Migration failed: {e}")
            return False
    finally:
        conn.close()

def downgrade(db_path='database/credstack.db'):
    """
    SQLite doesn't support DROP COLUMN easily.
    Would require recreating the table without those columns.
    """
    print("⚠ Downgrade not supported for SQLite ALTER TABLE operations")
    print("  To rollback, restore from backup or recreate the database")
    return False

if __name__ == '__main__':
    import os
    db_path = os.getenv('DATABASE_PATH', 'database/credstack.db')
    
    if len(sys.argv) > 1 and sys.argv[1] == 'down':
        downgrade(db_path)
    else:
        upgrade(db_path)
