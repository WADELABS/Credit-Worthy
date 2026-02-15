import unittest
import os
import tempfile
import sqlite3
import json
from app import app
import database
import auth

class TestAPI(unittest.TestCase):
    def setUp(self):
        """Set up test database and client"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        # Monkeypatch database path
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
                phone TEXT,
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
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE automations (
                id INTEGER PRIMARY KEY, 
                user_id INTEGER, 
                automation_type TEXT, 
                is_active INTEGER DEFAULT 1, 
                configuration TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
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
                status TEXT DEFAULT 'pending', 
                outcome TEXT,
                notes TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
        # Create a test user and get token
        self.test_email = 'testuser@example.com'
        self.test_password = 'password123'
        password_hash = auth.hash_password(self.test_password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, password_hash, name, notification_preference, automation_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.test_email, password_hash, 'Test User', 'email', 'basic'))
        self.test_user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate JWT token for authenticated requests
        self.token = auth.create_jwt_token(self.test_user_id, self.test_email)
        self.auth_headers = {'Authorization': f'Bearer {self.token}'}
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    # ============ Authentication API Tests ============
    
    def test_api_register_success(self):
        """Test API user registration"""
        response = self.client.post('/api/auth/register',
            json={
                'email': 'newuser@example.com',
                'password': 'password123',
                'name': 'New User'
            })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('user_id', data)
    
    def test_api_register_duplicate_email(self):
        """Test API registration fails with duplicate email"""
        response = self.client.post('/api/auth/register',
            json={
                'email': self.test_email,
                'password': 'password123'
            })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_register_weak_password(self):
        """Test API registration fails with weak password"""
        response = self.client.post('/api/auth/register',
            json={
                'email': 'user@example.com',
                'password': 'short'
            })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_login_success(self):
        """Test API login with correct credentials"""
        response = self.client.post('/api/auth/login',
            json={
                'email': self.test_email,
                'password': self.test_password
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('user_id', data)
    
    def test_api_login_wrong_password(self):
        """Test API login fails with wrong password"""
        response = self.client.post('/api/auth/login',
            json={
                'email': self.test_email,
                'password': 'wrongpassword'
            })
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_login_nonexistent_user(self):
        """Test API login fails for non-existent user"""
        response = self.client.post('/api/auth/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'password123'
            })
        
        self.assertEqual(response.status_code, 401)
    
    def test_api_token_refresh(self):
        """Test JWT token refresh"""
        response = self.client.post('/api/auth/token/refresh',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
    
    def test_api_token_refresh_unauthorized(self):
        """Test token refresh fails without authentication"""
        response = self.client.post('/api/auth/token/refresh')
        
        self.assertEqual(response.status_code, 401)
    
    # ============ Credit Score API Tests ============
    
    def test_api_credit_score(self):
        """Test credit score API endpoint"""
        # Add some accounts
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance, credit_limit)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Test Card', 'credit_card', 100.0, 1000.0))
        conn.commit()
        conn.close()
        
        response = self.client.get('/api/v1/credit/score',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('score', data)
        self.assertIn('utilization', data)
        self.assertIn('date', data)
        self.assertTrue(700 <= data['score'] <= 800)
    
    def test_api_credit_score_unauthorized(self):
        """Test credit score requires authentication"""
        response = self.client.get('/api/v1/credit/score')
        
        self.assertEqual(response.status_code, 401)
    
    def test_api_credit_accounts(self):
        """Test credit accounts API endpoint"""
        # Add accounts
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO accounts (user_id, name, account_type, balance, credit_limit)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Test Card', 'credit_card', 100.0, 1000.0))
        conn.commit()
        conn.close()
        
        response = self.client.get('/api/v1/credit/accounts',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Card')
    
    # ============ Automation API Tests ============
    
    def test_api_get_automation_rules(self):
        """Test get automation rules"""
        # Add automation rule
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO automations (user_id, automation_type, configuration)
            VALUES (?, ?, ?)
        ''', (self.test_user_id, 'statement_alert', 'Test config'))
        conn.commit()
        conn.close()
        
        response = self.client.get('/api/v1/automation/rules',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['automation_type'], 'statement_alert')
    
    def test_api_create_automation_rule(self):
        """Test create automation rule via API"""
        response = self.client.post('/api/v1/automation/rules',
            headers=self.auth_headers,
            json={
                'type': 'weekly_scan',
                'configuration': 'Scan every Friday'
            })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        
        # Verify in database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        auto = conn.execute('SELECT * FROM automations WHERE id = ?', (data['id'],)).fetchone()
        conn.close()
        
        self.assertIsNotNone(auto)
        self.assertEqual(auto['automation_type'], 'weekly_scan')
    
    def test_api_create_automation_rule_missing_type(self):
        """Test creating automation rule fails without type"""
        response = self.client.post('/api/v1/automation/rules',
            headers=self.auth_headers,
            json={'configuration': 'Some config'})
        
        self.assertEqual(response.status_code, 400)
    
    # ============ Disputes API Tests ============
    
    def test_api_get_disputes(self):
        """Test get disputes"""
        # Add dispute
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Experian', 'Test Bank', '2024-01-01', '2024-01-01', 'pending'))
        conn.commit()
        conn.close()
        
        response = self.client.get('/api/v1/disputes',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['bureau'], 'Experian')
    
    def test_api_get_disputes_with_filter(self):
        """Test get disputes with status filter"""
        # Add multiple disputes
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Experian', 'Test Bank', '2024-01-01', '2024-01-01', 'pending'))
        conn.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Equifax', 'Another Bank', '2024-01-02', '2024-01-02', 'resolved'))
        conn.commit()
        conn.close()
        
        response = self.client.get('/api/v1/disputes?status=pending',
            headers=self.auth_headers)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['status'], 'pending')
    
    def test_api_create_dispute(self):
        """Test create dispute via API"""
        response = self.client.post('/api/v1/disputes',
            headers=self.auth_headers,
            json={
                'bureau': 'TransUnion',
                'creditor': 'Test Creditor',
                'reason': 'Incorrect balance',
                'notes': 'Balance should be $0'
            })
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertIn('follow_up_date', data)
    
    def test_api_create_dispute_missing_required(self):
        """Test creating dispute fails without required fields"""
        response = self.client.post('/api/v1/disputes',
            headers=self.auth_headers,
            json={'reason': 'Some reason'})
        
        self.assertEqual(response.status_code, 400)
    
    def test_api_get_dispute_detail(self):
        """Test get specific dispute"""
        # Add dispute
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Experian', 'Test Bank', '2024-01-01', '2024-01-01', 'pending'))
        dispute_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        response = self.client.get(f'/api/v1/disputes/{dispute_id}',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], dispute_id)
        self.assertEqual(data['bureau'], 'Experian')
    
    def test_api_update_dispute(self):
        """Test update dispute status"""
        # Add dispute
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Experian', 'Test Bank', '2024-01-01', '2024-01-01', 'pending'))
        dispute_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        response = self.client.put(f'/api/v1/disputes/{dispute_id}',
            headers=self.auth_headers,
            json={
                'status': 'resolved',
                'outcome': 'Removed from report'
            })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        dispute = conn.execute('SELECT * FROM disputes WHERE id = ?', (dispute_id,)).fetchone()
        conn.close()
        
        self.assertEqual(dispute['status'], 'resolved')
        self.assertEqual(dispute['outcome'], 'Removed from report')
        self.assertIsNotNone(dispute['date_resolved'])
    
    def test_api_delete_dispute(self):
        """Test delete dispute"""
        # Add dispute
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.test_user_id, 'Experian', 'Test Bank', '2024-01-01', '2024-01-01', 'pending'))
        dispute_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        response = self.client.delete(f'/api/v1/disputes/{dispute_id}',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        conn = sqlite3.connect(self.db_path)
        dispute = conn.execute('SELECT * FROM disputes WHERE id = ?', (dispute_id,)).fetchone()
        conn.close()
        
        self.assertIsNone(dispute)
    
    def test_api_dispute_not_found(self):
        """Test accessing non-existent dispute returns 404"""
        response = self.client.get('/api/v1/disputes/99999',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 404)
    
    # ============ User Profile API Tests ============
    
    def test_api_get_user_profile(self):
        """Test get user profile"""
        response = self.client.get('/api/v1/user/profile',
            headers=self.auth_headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'], self.test_email)
        self.assertEqual(data['name'], 'Test User')
    
    def test_api_update_user_profile(self):
        """Test update user profile"""
        response = self.client.put('/api/v1/user/profile',
            headers=self.auth_headers,
            json={
                'name': 'Updated Name',
                'phone': '+15551234567',
                'notification_preference': 'sms'
            })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM users WHERE id = ?', (self.test_user_id,)).fetchone()
        conn.close()
        
        self.assertEqual(user['name'], 'Updated Name')
        self.assertEqual(user['phone'], '+15551234567')
        self.assertEqual(user['notification_preference'], 'sms')
    
    # ============ Data Isolation Tests ============
    
    def test_api_data_isolation(self):
        """Test users can only access their own data"""
        # Create another user
        password_hash = auth.hash_password('password456')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('other@example.com', password_hash, 'email', 'basic'))
        other_user_id = cursor.lastrowid
        
        # Add dispute for other user
        cursor.execute('''
            INSERT INTO disputes (user_id, bureau, creditor, dispute_date, date_filed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (other_user_id, 'Experian', 'Test Bank', '2024-01-01', '2024-01-01', 'pending'))
        other_dispute_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Try to access other user's dispute with first user's token
        response = self.client.get(f'/api/v1/disputes/{other_dispute_id}',
            headers=self.auth_headers)
        
        # Should return 404 (not found) for security
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
