import unittest
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
import jwt
from app import app
import database
import auth

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        """Set up test database and client"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
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
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY, 
                user_id INTEGER, 
                reminder_type TEXT, 
                reminder_date TEXT, 
                message TEXT, 
                is_sent INTEGER, 
                created_at TIMESTAMP
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
    
    # ============ Password Validation Tests ============
    
    def test_password_validation_length(self):
        """Test password must meet minimum length"""
        is_valid, error = auth.validate_password("short")
        self.assertFalse(is_valid)
        self.assertIn("at least", error)
    
    def test_password_validation_requires_letter(self):
        """Test password must contain a letter"""
        is_valid, error = auth.validate_password("12345678")
        self.assertFalse(is_valid)
        self.assertIn("letter", error)
    
    def test_password_validation_requires_number(self):
        """Test password must contain a number"""
        is_valid, error = auth.validate_password("onlyletters")
        self.assertFalse(is_valid)
        self.assertIn("number", error)
    
    def test_password_validation_valid(self):
        """Test valid password passes validation"""
        is_valid, error = auth.validate_password("password123")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    # ============ Email Validation Tests ============
    
    def test_email_validation_missing_at(self):
        """Test email must contain @ symbol"""
        is_valid, error = auth.validate_email("notanemail.com")
        self.assertFalse(is_valid)
    
    def test_email_validation_missing_dot(self):
        """Test email must contain . symbol"""
        is_valid, error = auth.validate_email("notan@email")
        self.assertFalse(is_valid)
    
    def test_email_validation_too_long(self):
        """Test email cannot exceed maximum length"""
        long_email = "a" * 250 + "@example.com"
        is_valid, error = auth.validate_email(long_email)
        self.assertFalse(is_valid)
    
    def test_email_validation_valid(self):
        """Test valid email passes validation"""
        is_valid, error = auth.validate_email("user@example.com")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    # ============ Password Hashing Tests ============
    
    def test_password_hashing(self):
        """Test password is properly hashed"""
        password = "mypassword123"
        hashed = auth.hash_password(password)
        
        # Hash should be different from password
        self.assertNotEqual(password, hashed)
        
        # Hash should be bcrypt format (starts with $2b$)
        self.assertTrue(hashed.startswith('$2b$'))
    
    def test_password_verification_correct(self):
        """Test correct password verifies successfully"""
        password = "mypassword123"
        hashed = auth.hash_password(password)
        
        self.assertTrue(auth.verify_password(password, hashed))
    
    def test_password_verification_incorrect(self):
        """Test incorrect password fails verification"""
        password = "mypassword123"
        hashed = auth.hash_password(password)
        
        self.assertFalse(auth.verify_password("wrongpassword", hashed))
    
    # ============ Registration Tests ============
    
    def test_registration_success(self):
        """Test successful user registration"""
        response = self.client.post('/register', data={
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'name': 'Test User'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to CredStack', response.data)
        
        # Verify user was created in database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT * FROM users WHERE email = ?', ('newuser@example.com',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'newuser@example.com')
        self.assertIsNotNone(user['password_hash'])
    
    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email"""
        # Create first user
        self.client.post('/register', data={
            'email': 'user@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        })
        
        # Try to create another user with same email
        response = self.client.post('/register', data={
            'email': 'user@example.com',
            'password': 'password456',
            'password_confirm': 'password456'
        }, follow_redirects=True)
        
        self.assertIn(b'already registered', response.data)
    
    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match"""
        response = self.client.post('/register', data={
            'email': 'user@example.com',
            'password': 'password123',
            'password_confirm': 'different456'
        }, follow_redirects=True)
        
        self.assertIn(b'do not match', response.data)
    
    def test_registration_weak_password(self):
        """Test registration fails with weak password"""
        response = self.client.post('/register', data={
            'email': 'user@example.com',
            'password': 'short',
            'password_confirm': 'short'
        }, follow_redirects=True)
        
        self.assertIn(b'at least', response.data)
    
    # ============ Login Tests ============
    
    def test_login_success(self):
        """Test successful login with correct credentials"""
        # Register user first
        password = 'password123'
        password_hash = auth.hash_password(password)
        
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('user@example.com', password_hash, 'email', 'basic'))
        conn.commit()
        conn.close()
        
        # Try to login
        response = self.client.post('/login', data={
            'email': 'user@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
    
    def test_login_wrong_password(self):
        """Test login fails with incorrect password"""
        # Register user
        password_hash = auth.hash_password('password123')
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('user@example.com', password_hash, 'email', 'basic'))
        conn.commit()
        conn.close()
        
        # Try to login with wrong password
        response = self.client.post('/login', data={
            'email': 'user@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_login_nonexistent_user(self):
        """Test login fails for non-existent user"""
        response = self.client.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_login_account_lockout(self):
        """Test account locks after multiple failed attempts"""
        # Register user
        password_hash = auth.hash_password('password123')
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level, failed_login_attempts)
            VALUES (?, ?, ?, ?, ?)
        ''', ('user@example.com', password_hash, 'email', 'basic', 2))
        conn.commit()
        conn.close()
        
        # Attempt login with wrong password (3rd failed attempt)
        response = self.client.post('/login', data={
            'email': 'user@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertIn(b'locked', response.data)
    
    def test_login_resets_failed_attempts_on_success(self):
        """Test failed login counter resets after successful login"""
        # Register user with some failed attempts
        password_hash = auth.hash_password('password123')
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level, failed_login_attempts)
            VALUES (?, ?, ?, ?, ?)
        ''', ('user@example.com', password_hash, 'email', 'basic', 2))
        conn.commit()
        conn.close()
        
        # Login with correct password
        response = self.client.post('/login', data={
            'email': 'user@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check failed attempts were reset
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        user = conn.execute('SELECT failed_login_attempts FROM users WHERE email = ?', 
                          ('user@example.com',)).fetchone()
        conn.close()
        
        self.assertEqual(user['failed_login_attempts'], 0)
    
    # ============ JWT Token Tests ============
    
    def test_jwt_token_creation(self):
        """Test JWT token is created correctly"""
        token = auth.create_jwt_token(1, 'user@example.com')
        
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 50)
    
    def test_jwt_token_decode(self):
        """Test JWT token can be decoded"""
        user_id = 123
        email = 'user@example.com'
        token = auth.create_jwt_token(user_id, email)
        
        decoded_id, decoded_email = auth.decode_jwt_token(token)
        
        self.assertEqual(decoded_id, user_id)
        self.assertEqual(decoded_email, email)
    
    def test_jwt_token_invalid(self):
        """Test invalid JWT token returns error"""
        user_id, error = auth.decode_jwt_token("invalid.token.here")
        
        self.assertIsNone(user_id)
        self.assertIsNotNone(error)
    
    # ============ API Token Tests ============
    
    def test_generate_api_token(self):
        """Test API token generation"""
        token = auth.generate_api_token()
        
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)
    
    # ============ Additional Negative Test Cases ============
    
    def test_login_with_empty_email(self):
        """Test login fails with empty email"""
        response = self.client.post('/login', data={
            'email': '',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertIn(b'required', response.data.lower())
    
    def test_login_with_empty_password(self):
        """Test login fails with empty password"""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': ''
        }, follow_redirects=True)
        
        self.assertIn(b'required', response.data.lower())
    
    def test_login_with_empty_credentials(self):
        """Test login fails with both fields empty"""
        response = self.client.post('/login', data={
            'email': '',
            'password': ''
        }, follow_redirects=True)
        
        self.assertIn(b'required', response.data.lower())
    
    def test_login_sql_injection_attempt(self):
        """Test SQL injection in login is prevented"""
        malicious_inputs = [
            "admin' --",
            "admin'/*",
            "' OR '1'='1",
            "1' UNION SELECT NULL--",
            "admin' OR 1=1--"
        ]
        
        for malicious in malicious_inputs:
            response = self.client.post('/login', data={
                'email': malicious,
                'password': 'password'
            }, follow_redirects=True)
            
            # Should fail gracefully, not expose database
            self.assertNotIn(b'syntax error', response.data.lower())
            self.assertNotIn(b'sqlite', response.data.lower())
    
    def test_registration_with_invalid_email_formats(self):
        """Test registration handles various invalid email formats"""
        # Test the most clearly invalid email
        response = self.client.post('/register', data={
            'email': 'notanemail',
            'password': 'password123',
            'password_confirm': 'password123'
        }, follow_redirects=True)
        
        # Should show error message
        self.assertIn(b'Invalid email', response.data)
    
    def test_logout_clears_session(self):
        """Test logout functionality clears user session"""
        # First login
        password_hash = auth.hash_password('password123')
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('user@example.com', password_hash, 'email', 'basic'))
        conn.commit()
        conn.close()
        
        self.client.post('/login', data={
            'email': 'user@example.com',
            'password': 'password123'
        })
        
        # Then logout
        response = self.client.get('/logout', follow_redirects=True)
        
        # Should redirect to index
        self.assertEqual(response.status_code, 200)
        
        # Try to access protected route - should fail
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'log in', response.data.lower())
    
    def test_access_protected_route_without_login(self):
        """Test accessing protected route without authentication"""
        response = self.client.get('/dashboard', follow_redirects=True)
        
        # Should redirect to login page
        self.assertIn(b'log in', response.data.lower())
    
    def test_jwt_token_expiration(self):
        """Test expired JWT token is rejected"""
        # Create token with negative expiration (already expired)
        import jwt
        from datetime import timezone
        
        payload = {
            'user_id': 1,
            'email': 'test@example.com',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(payload, auth.JWT_SECRET, algorithm=auth.JWT_ALGORITHM)
        
        # Try to decode
        user_id, error = auth.decode_jwt_token(expired_token)
        
        self.assertIsNone(user_id)
        self.assertIsNotNone(error)
        self.assertIn('expired', error.lower())
    
    def test_account_lockout_duration_progressive(self):
        """Test account lockout duration increases with attempts"""
        # Test progressive lockout
        duration_3 = auth.calculate_lockout_duration(3)
        duration_4 = auth.calculate_lockout_duration(4)
        duration_7 = auth.calculate_lockout_duration(7)
        
        # Each should be progressively longer
        self.assertLess(duration_3, duration_4)
        self.assertLess(duration_4, duration_7)
    
    def test_check_account_locked_unlocked_account(self):
        """Test checking unlocked account"""
        # Create user without lock
        password_hash = auth.hash_password('password123')
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('user@example.com', password_hash, 'email', 'basic'))
        conn.commit()
        
        user = conn.execute('SELECT * FROM users WHERE email = ?', ('user@example.com',)).fetchone()
        conn.close()
        
        is_locked, unlock_time = auth.check_account_locked(user)
        
        self.assertFalse(is_locked)
        self.assertIsNone(unlock_time)
    
    def test_password_hash_is_salted(self):
        """Test password hashes are salted (different each time)"""
        password = "samepassword123"
        
        hash1 = auth.hash_password(password)
        hash2 = auth.hash_password(password)
        
        # Same password should produce different hashes due to salt
        self.assertNotEqual(hash1, hash2)
        
        # But both should verify correctly
        self.assertTrue(auth.verify_password(password, hash1))
        self.assertTrue(auth.verify_password(password, hash2))
