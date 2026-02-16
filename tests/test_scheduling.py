"""
Tests for scheduling and automation functionality
"""
import unittest
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import automation
import database


class TestScheduling(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        database.DB_PATH = self.db_path
        
        # Create tables
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                name TEXT,
                notification_preference TEXT,
                automation_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                account_type TEXT,
                balance REAL,
                credit_limit REAL,
                statement_date INTEGER,
                due_date INTEGER,
                min_payment REAL,
                last_updated TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                reminder_type TEXT,
                reminder_date TEXT,
                message TEXT,
                is_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE automations (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                automation_type TEXT,
                is_active INTEGER DEFAULT 1,
                configuration TEXT,
                created_at TIMESTAMP,
                last_run TIMESTAMP
            )
        ''')
        
        # Create test user
        cursor.execute(
            'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
            ('test@example.com', 'hash123', 'Test User')
        )
        self.user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_calculate_next_date_current_month(self):
        """Test calculating next date in current month"""
        today = datetime.now()
        # Use a day that's after today
        day_of_month = (today.day + 5) if today.day <= 25 else 5
        
        result = automation.calculate_next_date(day_of_month)
        
        # Should be in the future
        self.assertGreater(result, today)
        # Should have correct day
        self.assertEqual(result.day, day_of_month)
    
    def test_calculate_next_date_next_month(self):
        """Test calculating next date when it's in next month"""
        today = datetime.now()
        # Use a day that's before today
        day_of_month = today.day - 1 if today.day > 1 else 28
        
        result = automation.calculate_next_date(day_of_month)
        
        # Should be in the future
        self.assertGreater(result, today)
        # Should be next month
        expected_month = (today.month % 12) + 1 if today.day >= day_of_month else today.month
        self.assertEqual(result.day, day_of_month)
    
    def test_calculate_next_date_with_months_ahead(self):
        """Test calculating date with months ahead"""
        today = datetime.now()
        day_of_month = 15
        months_ahead = 2
        
        result = automation.calculate_next_date(day_of_month, months_ahead)
        
        # Should be roughly 2 months in the future
        self.assertGreater(result, today + timedelta(days=50))
        self.assertEqual(result.day, day_of_month)
    
    def test_calculate_next_date_end_of_month(self):
        """Test calculating date for 31st when month doesn't have 31 days"""
        result = automation.calculate_next_date(31)
        
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertGreater(result, datetime.now())
    
    def test_generate_statement_alert(self):
        """Test generating statement alert"""
        conn = database.get_db()
        
        # Create an account with statement date
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance, credit_limit, statement_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.user_id, 'Test Card', 'credit_card', 1000.0, 5000.0, 15))
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate alert
        automation.generate_statement_alert(self.user_id, account_id, 'Test Card', 15)
        
        # Check reminder was created
        conn = database.get_db()
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ? AND message LIKE ?',
            (self.user_id, '%Test Card%')
        ).fetchall()
        conn.close()
        
        self.assertEqual(len(reminders), 1)
        self.assertIn('statement closes', reminders[0]['message'])
        self.assertIn('Test Card', reminders[0]['message'])
    
    def test_generate_statement_alert_no_duplicate(self):
        """Test that duplicate alerts are not created"""
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date)
            VALUES (?, ?, ?, ?)
        ''', (self.user_id, 'Test Card', 'credit_card', 15))
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate alert twice
        automation.generate_statement_alert(self.user_id, account_id, 'Test Card', 15)
        automation.generate_statement_alert(self.user_id, account_id, 'Test Card', 15)
        
        # Check only one reminder exists
        conn = database.get_db()
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ? AND message LIKE ?',
            (self.user_id, '%Test Card%')
        ).fetchall()
        conn.close()
        
        self.assertEqual(len(reminders), 1)
    
    def test_run_all_automations(self):
        """Test running all automations for a user"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Create multiple accounts with statement dates
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date)
            VALUES (?, ?, ?, ?)
        ''', (self.user_id, 'Card 1', 'credit_card', 15))
        
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date)
            VALUES (?, ?, ?, ?)
        ''', (self.user_id, 'Card 2', 'credit_card', 25))
        
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date)
            VALUES (?, ?, ?, ?)
        ''', (self.user_id, 'Card 3', 'credit_card', None))  # No statement date
        
        conn.commit()
        conn.close()
        
        # Run automations
        automation.run_all_automations(self.user_id)
        
        # Check reminders were created for accounts with statement dates
        conn = database.get_db()
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?',
            (self.user_id,)
        ).fetchall()
        conn.close()
        
        # Should have 2 reminders (Card 1 and Card 2, but not Card 3)
        self.assertEqual(len(reminders), 2)
    
    def test_create_automated_reminder_simple(self):
        """Test creating simple automated reminder"""
        automation.create_automated_reminder(
            self.user_id,
            'test_reminder',
            'Test reminder message',
            days_before=5
        )
        
        conn = database.get_db()
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?',
            (self.user_id,)
        ).fetchall()
        conn.close()
        
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]['message'], 'Test reminder message')
        self.assertEqual(reminders[0]['reminder_type'], 'test_reminder')
    
    def test_create_automated_reminder_with_reference_date(self):
        """Test creating automated reminder with reference date"""
        today = datetime.now()
        # Use a day that makes sense for the current month
        reference_day = 15
        
        automation.create_automated_reminder(
            self.user_id,
            'monthly_reminder',
            'Monthly task',
            days_before=3,
            reference_date=reference_day
        )
        
        conn = database.get_db()
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?',
            (self.user_id,)
        ).fetchall()
        conn.close()
        
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]['message'], 'Monthly task')
        
        # Parse reminder date
        reminder_date = datetime.strptime(reminders[0]['reminder_date'], '%Y-%m-%d')
        
        # Should be in the future
        self.assertGreaterEqual(reminder_date, today.replace(hour=0, minute=0, second=0, microsecond=0))
    
    def test_create_automated_reminder_end_of_month(self):
        """Test creating reminder for end of month"""
        automation.create_automated_reminder(
            self.user_id,
            'monthly_reminder',
            'End of month task',
            days_before=2,
            reference_date=31  # End of month
        )
        
        conn = database.get_db()
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?',
            (self.user_id,)
        ).fetchall()
        conn.close()
        
        self.assertEqual(len(reminders), 1)
        # Should handle gracefully even in months without 31 days
        self.assertIsNotNone(reminders[0]['reminder_date'])
    
    def test_load_config_default(self):
        """Test loading default config when file doesn't exist"""
        # Config should be loaded at module level
        config = automation.config
        
        self.assertIn('automation', config)
        self.assertIn('utilization', config['automation'])
        self.assertIn('target_maximum', config['automation']['utilization'])
        self.assertEqual(config['automation']['utilization']['target_maximum'], 10.0)


class TestConcurrentAutomation(unittest.TestCase):
    """Test concurrent automation scenarios"""
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        database.DB_PATH = self.db_path
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                name TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE accounts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                account_type TEXT,
                statement_date INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                reminder_type TEXT,
                reminder_date TEXT,
                message TEXT
            )
        ''')
        
        # Create multiple users
        for i in range(3):
            cursor.execute(
                'INSERT INTO users (email, name) VALUES (?, ?)',
                (f'user{i}@example.com', f'User {i}')
            )
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_multiple_users_automation(self):
        """Test running automation for multiple users"""
        conn = database.get_db()
        cursor = conn.cursor()
        
        # Add accounts for each user
        for user_id in [1, 2, 3]:
            cursor.execute('''
                INSERT INTO accounts (user_id, name, account_type, statement_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, f'Card User {user_id}', 'credit_card', 15))
        
        conn.commit()
        conn.close()
        
        # Run automation for all users
        for user_id in [1, 2, 3]:
            automation.run_all_automations(user_id)
        
        # Check each user has their reminders
        conn = database.get_db()
        for user_id in [1, 2, 3]:
            reminders = conn.execute(
                'SELECT * FROM reminders WHERE user_id = ?',
                (user_id,)
            ).fetchall()
            self.assertEqual(len(reminders), 1)
            self.assertIn(f'Card User {user_id}', reminders[0]['message'])
        
        conn.close()


if __name__ == '__main__':
    unittest.main()
