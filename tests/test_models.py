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
    
    def test_account_creation(self):
        """Test creating an account"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user first
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create account
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance, credit_limit)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'Test Card', 'credit_card', 1000.50, 5000.00))
        
        account_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve account
        account = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
        conn.close()
        
        self.assertEqual(account['name'], 'Test Card')
        self.assertEqual(account['account_type'], 'credit_card')
        self.assertEqual(float(account['balance']), 1000.50)
        self.assertEqual(float(account['credit_limit']), 5000.00)
    
    def test_user_account_relationship(self):
        """Test relationship between users and accounts"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create multiple accounts for user
        for i in range(3):
            cursor.execute('''
                INSERT INTO accounts (user_id, name, account_type)
                VALUES (?, ?, ?)
            ''', (user_id, f'Card {i}', 'credit_card'))
        
        conn.commit()
        
        # Retrieve all accounts for user
        accounts = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?',
            (user_id,)
        ).fetchall()
        conn.close()
        
        self.assertEqual(len(accounts), 3)
        for i, account in enumerate(accounts):
            self.assertEqual(account['name'], f'Card {i}')
            self.assertEqual(account['user_id'], user_id)
    
    def test_automation_creation(self):
        """Test creating automation"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create automation
        cursor.execute('''
            INSERT INTO automations (user_id, automation_type, configuration)
            VALUES (?, ?, ?)
        ''', (user_id, 'statement_alert', 'Lead time: 3 days'))
        
        automation_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve automation
        automation = conn.execute('SELECT * FROM automations WHERE id = ?', (automation_id,)).fetchone()
        conn.close()
        
        self.assertEqual(automation['automation_type'], 'statement_alert')
        self.assertEqual(automation['is_active'], 1)
        self.assertEqual(automation['configuration'], 'Lead time: 3 days')
    
    def test_reminder_creation(self):
        """Test creating reminder"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create reminder
        cursor.execute('''
            INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
            VALUES (?, ?, ?, ?)
        ''', (user_id, 'payment', '2024-12-31', 'Pay your bill'))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve reminder
        reminder = conn.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,)).fetchone()
        conn.close()
        
        self.assertEqual(reminder['reminder_type'], 'payment')
        self.assertEqual(reminder['message'], 'Pay your bill')
        self.assertEqual(reminder['is_sent'], 0)
    
    def test_dispute_creation(self):
        """Test creating dispute"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create dispute
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, account_name, dispute_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'Experian', 'Chase Card', '2024-01-15', 'pending'))
        
        dispute_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve dispute
        dispute = conn.execute('SELECT * FROM disputes WHERE id = ?', (dispute_id,)).fetchone()
        conn.close()
        
        self.assertEqual(dispute['bureau'], 'Experian')
        self.assertEqual(dispute['account_name'], 'Chase Card')
        self.assertEqual(dispute['status'], 'pending')
    
    def test_user_cascade_operations(self):
        """Test that related records are accessible when user exists"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create related records
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (user_id, 'Test Card', 'credit_card'))
        
        cursor.execute('''
            INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
            VALUES (?, ?, ?, ?)
        ''', (user_id, 'test', '2024-12-31', 'Test reminder'))
        
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
