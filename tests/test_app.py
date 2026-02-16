import unittest
import os
import tempfile
import sqlite3
from app import app
import database
import auth

class TestCredStackApp(unittest.TestCase):
    def setUp(self):
        # Create a temp database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['DATABASE'] = self.db_path
        self.client = app.test_client()

        # Initialize the temp database
        # We need to monkeypatch database.DB_PATH for the test
        database.DB_PATH = self.db_path
        
        # Manually run the setup logic to create tables
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY, 
                email TEXT, 
                password_hash TEXT,
                name TEXT,
                notification_preference TEXT, 
                automation_level TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        cursor.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, account_type TEXT, balance REAL, credit_limit REAL, statement_date INTEGER, due_date INTEGER, min_payment REAL, last_updated TIMESTAMP)')
        cursor.execute('CREATE TABLE automations (id INTEGER PRIMARY KEY, user_id INTEGER, automation_type TEXT, is_active INTEGER, configuration TEXT, created_at TIMESTAMP, last_run TIMESTAMP)')
        cursor.execute('CREATE TABLE reminders (id INTEGER PRIMARY KEY, user_id INTEGER, reminder_type TEXT, reminder_date TEXT, message TEXT, is_sent INTEGER, created_at TIMESTAMP)')
        cursor.execute('CREATE TABLE disputes (id INTEGER PRIMARY KEY, user_id INTEGER, bureau TEXT, account_name TEXT, dispute_date TEXT, follow_up_date TEXT, status TEXT, notes TEXT, created_at TIMESTAMP)')
        
        # Create a test user with password
        password_hash = auth.hash_password('testpass123')
        cursor.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('test@example.com', password_hash, 'email', 'basic'))
        
        conn.commit()
        conn.close()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_index_page(self):
        """Verify landing page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CredStack', response.data)

    def test_login_redirect(self):
        """Verify login creates session and redirects to dashboard"""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        self.assertIn(b'test@example.com', response.data)

    def test_add_account(self):
        """Verify account creation"""
        # Login first
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        response = self.client.post('/accounts/add', data={
            'name': 'Test Card',
            'account_type': 'credit_card',
            'balance': '100.00',
            'credit_limit': '1000.00',
            'statement_date': '15'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Card', response.data)

if __name__ == '__main__':
    unittest.main()
