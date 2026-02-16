"""
Tests for database models, relationships, and constraints
"""
import unittest
import os
import tempfile
import sqlite3
from datetime import datetime
import database


class TestModels(unittest.TestCase):
    """Test database models and relationships"""
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        database.DB_PATH = self.db_path
        
        # Create all tables
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                phone TEXT,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notification_preference TEXT DEFAULT 'email',
                automation_level TEXT DEFAULT 'basic',
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP,
                last_login TIMESTAMP,
                api_token TEXT,
                api_token_created TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                balance DECIMAL(10,2) DEFAULT 0,
                credit_limit DECIMAL(10,2),
                statement_date INTEGER,
                due_date INTEGER,
                min_payment DECIMAL(10,2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE automations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                automation_type TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                configuration TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder_type TEXT NOT NULL,
                reminder_date DATE NOT NULL,
                message TEXT,
                is_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE disputes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bureau TEXT NOT NULL,
                account_name TEXT,
                creditor TEXT,
                reason TEXT,
                dispute_date DATE NOT NULL,
                date_filed DATE,
                follow_up_date DATE,
                date_resolved DATE,
                status TEXT DEFAULT 'pending',
                outcome TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_user_creation(self):
        """Test creating a user"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, name)
            VALUES (?, ?, ?)
        ''', ('test@example.com', 'hash123', 'Test User'))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve user
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        self.assertEqual(user['email'], 'test@example.com')
        self.assertEqual(user['name'], 'Test User')
        self.assertEqual(user['notification_preference'], 'email')
        self.assertEqual(user['automation_level'], 'basic')
    
    def test_user_email_unique_constraint(self):
        """Test that user email must be unique"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Insert first user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        conn.commit()
        
        # Try to insert duplicate email
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute('''
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
            ''', ('test@example.com', 'hash456'))
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
        ''', (user_id, 'test_automation'))
        
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, dispute_date)
            VALUES (?, ?, ?)
        ''', (user_id, 'Experian', '2024-01-15'))
        
        conn.commit()
        
        # Verify all records exist
        accounts = conn.execute('SELECT * FROM accounts WHERE user_id = ?', (user_id,)).fetchall()
        reminders = conn.execute('SELECT * FROM reminders WHERE user_id = ?', (user_id,)).fetchall()
        automations = conn.execute('SELECT * FROM automations WHERE user_id = ?', (user_id,)).fetchall()
        disputes = conn.execute('SELECT * FROM disputes WHERE user_id = ?', (user_id,)).fetchall()
        
        conn.close()
        
        self.assertEqual(len(accounts), 1)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(len(automations), 1)
        self.assertEqual(len(disputes), 1)
    
    def test_account_balance_calculations(self):
        """Test account balance and utilization calculations"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        # Create account with known balance and limit
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance, credit_limit)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'Test Card', 'credit_card', 1500.00, 5000.00))
        
        account_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve and calculate utilization
        account = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
        conn.close()
        
        balance = float(account['balance'])
        credit_limit = float(account['credit_limit'])
        utilization = (balance / credit_limit) * 100 if credit_limit > 0 else 0
        
        self.assertEqual(utilization, 30.0)  # 1500/5000 = 30%
    
    def test_database_connection(self):
        """Test database connection helper"""
        conn = database.get_db()
        
        # Should be able to execute queries
        result = conn.execute('SELECT 1 as test').fetchone()
        
        self.assertEqual(result['test'], 1)
        
        conn.close()
    
    def test_failed_login_tracking(self):
        """Test tracking failed login attempts"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user
        cursor.execute('''
            INSERT INTO users (email, password_hash, failed_login_attempts)
            VALUES (?, ?, ?)
        ''', ('test@example.com', 'hash123', 0))
        user_id = cursor.lastrowid
        conn.commit()
        
        # Increment failed attempts
        cursor.execute('''
            UPDATE users SET failed_login_attempts = failed_login_attempts + 1
            WHERE id = ?
        ''', (user_id,))
        conn.commit()
        
        # Check updated value
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        self.assertEqual(user['failed_login_attempts'], 1)
    
    def test_account_last_updated_timestamp(self):
        """Test that accounts have last_updated timestamp"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create user and account
        cursor.execute('''
            INSERT INTO users (email, password_hash)
            VALUES (?, ?)
        ''', ('test@example.com', 'hash123'))
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (user_id, 'Test Card', 'credit_card'))
        account_id = cursor.lastrowid
        conn.commit()
        
        # Retrieve account
        account = conn.execute('SELECT * FROM accounts WHERE id = ?', (account_id,)).fetchone()
        conn.close()
        
        # Should have timestamp
        self.assertIsNotNone(account['last_updated'])


if __name__ == '__main__':
    unittest.main()
