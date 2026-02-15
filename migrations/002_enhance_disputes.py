#!/usr/bin/env python3
"""
Migration: Enhance disputes table with additional fields
"""

import sqlite3
import sys

def upgrade(db_path='database/credstack.db'):
    """Add creditor, reason, date_resolved, and outcome fields to disputes"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add creditor field (alias for account_name for backward compatibility)
        cursor.execute('''
            ALTER TABLE disputes ADD COLUMN creditor TEXT
        ''')
        
        # Add reason field
        cursor.execute('''
            ALTER TABLE disputes ADD COLUMN reason TEXT
        ''')
        
        # Add date_filed (alias for dispute_date)
        cursor.execute('''
            ALTER TABLE disputes ADD COLUMN date_filed DATE
        ''')
        
        # Add date_resolved
        cursor.execute('''
            ALTER TABLE disputes ADD COLUMN date_resolved DATE
        ''')
        
        # Add outcome field
        cursor.execute('''
            ALTER TABLE disputes ADD COLUMN outcome TEXT
        ''')
        
        conn.commit()
        print("✓ Migration 002_enhance_disputes applied successfully")
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
    """
    print("⚠ Downgrade not supported for SQLite ALTER TABLE operations")
    return False

if __name__ == '__main__':
    import os
    db_path = os.getenv('DATABASE_PATH', 'database/credstack.db')
    
    if len(sys.argv) > 1 and sys.argv[1] == 'down':
        downgrade(db_path)
    else:
        upgrade(db_path)
