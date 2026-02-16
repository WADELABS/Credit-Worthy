"""
Integration tests for end-to-end user workflows
"""
import unittest
import os
import tempfile
import sqlite3
from app import app
import database
import auth


class TestIntegration(unittest.TestCase):
    """Test complete user workflows end-to-end"""
    
    def setUp(self):
        """Set up test database and client"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        database.DB_PATH = self.db_path
        
        # Create all tables
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
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP,
                last_login TIMESTAMP,
                api_token TEXT,
                api_token_created TIMESTAMP,
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
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE automations (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                automation_type TEXT,
                is_active INTEGER,
                configuration TEXT,
                created_at TIMESTAMP,
                last_run TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE disputes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                bureau TEXT,
                account_name TEXT,
                creditor TEXT,
                reason TEXT,
                dispute_date TEXT,
                date_filed TEXT,
                follow_up_date TEXT,
                date_resolved TEXT,
                status TEXT,
                outcome TEXT,
                notes TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_complete_user_journey(self):
        """Test complete user registration to account management workflow"""
        # Step 1: Register new user
        register_response = self.client.post('/register', data={
            'email': 'journey@example.com',
            'password': 'SecurePass123',
            'password_confirm': 'SecurePass123',
            'name': 'Journey User'
        }, follow_redirects=True)
        
        self.assertEqual(register_response.status_code, 200)
        
        # Verify user was created
        conn = database.get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?',
            ('journey@example.com',)
        ).fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'journey@example.com')
        conn.close()
        
        # Step 2: User should be logged in after registration
        # Try accessing dashboard
        dashboard_response = self.client.get('/dashboard')
        self.assertEqual(dashboard_response.status_code, 200)
        
        # Step 3: Add an account
        add_account_response = self.client.post('/accounts/add', data={
            'name': 'Journey Credit Card',
            'account_type': 'credit_card',
            'balance': '500.00',
            'credit_limit': '2000.00',
            'statement_date': '15',
            'due_date': '25'
        }, follow_redirects=True)
        
        self.assertEqual(add_account_response.status_code, 200)
        
        # Verify account was created
        conn = database.get_db()
        account = conn.execute(
            'SELECT * FROM accounts WHERE name = ?',
            ('Journey Credit Card',)
        ).fetchone()
        self.assertIsNotNone(account)
        self.assertEqual(float(account['balance']), 500.00)
        self.assertEqual(float(account['credit_limit']), 2000.00)
        conn.close()
        
        # Step 4: Add a dispute
        dispute_response = self.client.post('/disputes/add', data={
            'bureau': 'Experian',
            'account_name': 'Old Account'
        }, follow_redirects=True)
        
        self.assertEqual(dispute_response.status_code, 200)
        
        # Verify dispute was created
        conn = database.get_db()
        dispute = conn.execute(
            'SELECT * FROM disputes WHERE account_name = ?',
            ('Old Account',)
        ).fetchone()
        self.assertIsNotNone(dispute)
        self.assertEqual(dispute['bureau'], 'Experian')
        conn.close()
        
        # Step 5: Logout
        logout_response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)
        
        # Step 6: Verify cannot access dashboard after logout
        dashboard_after_logout = self.client.get('/dashboard', follow_redirects=True)
        # Should redirect to login page
        self.assertIn(b'Login', dashboard_after_logout.data)
    
    def test_api_workflow(self):
        """Test API registration and authentication workflow"""
        # Step 1: Register via API
        register_response = self.client.post('/api/auth/register', 
            json={
                'email': 'api@example.com',
                'password': 'ApiPass123',
                'name': 'API User'
            }
        )
        
        self.assertEqual(register_response.status_code, 201)
        data = register_response.get_json()
        self.assertIn('token', data)
        token = data['token']
        
        # Step 2: Use token to access protected API endpoint
        credit_response = self.client.get('/api/v1/credit/score',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(credit_response.status_code, 200)
        
        # Step 3: Login via API to get new token
        login_response = self.client.post('/api/auth/login',
            json={
                'email': 'api@example.com',
                'password': 'ApiPass123'
            }
        )
        
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.get_json()
        self.assertIn('token', login_data)


if __name__ == '__main__':
    unittest.main()
