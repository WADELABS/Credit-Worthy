"""
Database Model Tests
Tests for database models, relationships, constraints, and integrity
"""
import pytest
import sqlite3
from datetime import datetime
import database
import auth


class TestDatabaseModels:
    """Tests for database models and relationships"""
    
    def test_user_creation(self, test_db):
        """Test creating a user"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
        ''', ('user@example.com', 'hash123', 'Test User'))
        user_id = cursor.lastrowid
        conn.commit()
        
        # Verify user was created
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        assert user is not None
        assert user[1] == 'user@example.com'  # email
        assert user[2] == 'hash123'  # password_hash
        assert user[3] == 'Test User'  # name
    
    def test_user_email_unique_constraint(self, test_db):
        """Test that email must be unique"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create first user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('user@example.com', 'hash123'))
        conn.commit()
        
        # Try to create duplicate
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
            ''', ('user@example.com', 'hash456'))
            conn.commit()
        
        conn.close()
    
    def test_account_foreign_key_relationship(self, test_db, test_user):
        """Test account belongs to user"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create account for user
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance)
            VALUES (?, ?, ?, ?)
        ''', (test_user['id'], 'Test Card', 'credit_card', 100.0))
        account_id = cursor.lastrowid
        conn.commit()
        
        # Verify account exists
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        account = cursor.fetchone()
        conn.close()
        
        assert account is not None
        assert account[1] == test_user['id']  # user_id
        assert account[2] == 'Test Card'  # name
    
    def test_cascade_delete_accounts(self, test_db, test_user):
        """Test that deleting a user cascades to accounts"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create account for user
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance)
            VALUES (?, ?, ?, ?)
        ''', (test_user['id'], 'Test Card', 'credit_card', 100.0))
        account_id = cursor.lastrowid
        conn.commit()
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (test_user['id'],))
        conn.commit()
        
        # Verify account was also deleted
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        account = cursor.fetchone()
        conn.close()
        
        assert account is None
    
    def test_cascade_delete_automations(self, test_db, test_user):
        """Test that deleting a user cascades to automations"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create automation for user
        cursor.execute('''
            INSERT INTO automations (user_id, automation_type, configuration)
            VALUES (?, ?, ?)
        ''', (test_user['id'], 'statement_alert', 'config'))
        automation_id = cursor.lastrowid
        conn.commit()
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (test_user['id'],))
        conn.commit()
        
        # Verify automation was also deleted
        cursor.execute('SELECT * FROM automations WHERE id = ?', (automation_id,))
        automation = cursor.fetchone()
        conn.close()
        
        assert automation is None
    
    def test_cascade_delete_disputes(self, test_db, test_user):
        """Test that deleting a user cascades to disputes"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create dispute for user
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, status)
            VALUES (?, ?, ?, ?)
        ''', (test_user['id'], 'Experian', 'Test Bank', 'pending'))
        dispute_id = cursor.lastrowid
        conn.commit()
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (test_user['id'],))
        conn.commit()
        
        # Verify dispute was also deleted
        cursor.execute('SELECT * FROM disputes WHERE id = ?', (dispute_id,))
        dispute = cursor.fetchone()
        conn.close()
        
        assert dispute is None
    
    def test_reminder_creation_with_defaults(self, test_db, test_user):
        """Test reminder creation with default values"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
            VALUES (?, ?, ?, ?)
        ''', (test_user['id'], 'automation', '2024-12-25', 'Test reminder'))
        reminder_id = cursor.lastrowid
        conn.commit()
        
        # Verify reminder with defaults
        cursor.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,))
        reminder = cursor.fetchone()
        conn.close()
        
        assert reminder is not None
        assert reminder[5] == 0  # is_sent should default to 0
        assert reminder[6] is not None  # created_at should be set
    
    def test_account_with_nullable_fields(self, test_db, test_user):
        """Test account creation with nullable fields"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create account with minimal data
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (test_user['id'], 'Basic Account', 'savings'))
        account_id = cursor.lastrowid
        conn.commit()
        
        # Verify account was created
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        account = cursor.fetchone()
        conn.close()
        
        assert account is not None
        assert account[2] == 'Basic Account'
        assert account[4] is None  # balance is NULL
        assert account[5] is None  # credit_limit is NULL
    
    def test_dispute_status_default(self, test_db, test_user):
        """Test dispute status defaults to pending"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, creditor)
            VALUES (?, ?, ?)
        ''', (test_user['id'], 'TransUnion', 'Test Creditor'))
        dispute_id = cursor.lastrowid
        conn.commit()
        
        # Verify status defaults
        cursor.execute('SELECT status FROM disputes WHERE id = ?', (dispute_id,))
        status = cursor.fetchone()[0]
        conn.close()
        
        assert status == 'pending'
    
    def test_automation_is_active_default(self, test_db, test_user):
        """Test automation is_active defaults to 1 (true)"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO automations (user_id, automation_type)
            VALUES (?, ?)
        ''', (test_user['id'], 'weekly_scan'))
        automation_id = cursor.lastrowid
        conn.commit()
        
        # Verify is_active defaults
        cursor.execute('SELECT is_active FROM automations WHERE id = ?', (automation_id,))
        is_active = cursor.fetchone()[0]
        conn.close()
        
        assert is_active == 1
    
    def test_user_failed_login_attempts_default(self, test_db):
        """Test user failed_login_attempts defaults to 0"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash'))
        user_id = cursor.lastrowid
        conn.commit()
        
        # Verify default
        cursor.execute('SELECT failed_login_attempts FROM users WHERE id = ?', (user_id,))
        attempts = cursor.fetchone()[0]
        conn.close()
        
        assert attempts == 0
    
    def test_multiple_accounts_per_user(self, test_db, test_user):
        """Test user can have multiple accounts"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create multiple accounts
        for i in range(3):
            cursor.execute('''
                INSERT INTO accounts (user_id, name, account_type)
                VALUES (?, ?, ?)
            ''', (test_user['id'], f'Account {i}', 'credit_card'))
        conn.commit()
        
        # Verify all accounts
        cursor.execute('SELECT COUNT(*) FROM accounts WHERE user_id = ?', (test_user['id'],))
        count = cursor.fetchone()[0]
        conn.close()
        
        assert count == 3
    
    def test_data_integrity_numeric_fields(self, test_db, test_user):
        """Test numeric fields store correct data types"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create account with specific numeric values
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance, credit_limit)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_user['id'], 'Test', 'credit_card', 1234.56, 5000.00))
        account_id = cursor.lastrowid
        conn.commit()
        
        # Verify numeric precision
        cursor.execute('SELECT balance, credit_limit FROM accounts WHERE id = ?', (account_id,))
        balance, credit_limit = cursor.fetchone()
        conn.close()
        
        assert balance == 1234.56
        assert credit_limit == 5000.00
    
    def test_timestamp_fields(self, test_db, test_user):
        """Test timestamp fields are properly stored"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create account
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (test_user['id'], 'Test', 'credit_card'))
        account_id = cursor.lastrowid
        conn.commit()
        
        # Verify last_updated timestamp
        cursor.execute('SELECT last_updated FROM accounts WHERE id = ?', (account_id,))
        last_updated = cursor.fetchone()[0]
        conn.close()
        
        assert last_updated is not None


class TestDatabaseHelpers:
    """Tests for database helper functions"""
    
    def test_get_db_connection(self, test_db):
        """Test getting a database connection"""
        conn = database.get_db()
        assert conn is not None
        
        # Verify it's a sqlite3 connection
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        assert len(tables) > 0
    
    def test_database_path_configuration(self, test_db):
        """Test database path can be configured"""
        original_path = database.DB_PATH
        
        # Path should be set to test database
        assert database.DB_PATH == test_db
        
        # Restore original path
        database.DB_PATH = original_path
