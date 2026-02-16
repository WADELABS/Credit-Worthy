"""
Shared fixtures and test configuration for pytest
"""
import os
import tempfile
import sqlite3
import pytest
from app import app as flask_app
import database
import auth

# Disable rate limiting for all tests
os.environ['RATELIMIT_ENABLED'] = 'false'


@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app instance for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Disable rate limiting for tests
    flask_app.config['RATELIMIT_ENABLED'] = False
    
    yield flask_app


@pytest.fixture(scope='function')
def client(app, test_db):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture(scope='function')
def test_db():
    """Create a temporary test database"""
    db_fd, db_path = tempfile.mkstemp()
    database.DB_PATH = db_path
    
    # Create all tables
    conn = sqlite3.connect(db_path)
    
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    
    cursor = conn.cursor()
    
    # Users table
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
    
    # Accounts table
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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Automations table
    cursor.execute('''
        CREATE TABLE automations (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            automation_type TEXT, 
            is_active INTEGER DEFAULT 1, 
            configuration TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            last_run TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Reminders table
    cursor.execute('''
        CREATE TABLE reminders (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            reminder_type TEXT, 
            reminder_date TEXT, 
            message TEXT, 
            is_sent INTEGER DEFAULT 0, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Disputes table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def test_user(test_db):
    """Create a test user and return user data"""
    email = 'test@example.com'
    password = 'password123'
    password_hash = auth.hash_password(password)
    
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, password_hash, name, notification_preference, automation_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, password_hash, 'Test User', 'email', 'basic'))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'id': user_id,
        'email': email,
        'password': password,
        'password_hash': password_hash
    }


@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Create an authenticated test client"""
    # Login the test user
    client.post('/login', data={
        'email': test_user['email'],
        'password': test_user['password']
    })
    return client


@pytest.fixture(scope='function')
def auth_token(test_user):
    """Generate a JWT token for API testing"""
    return auth.create_jwt_token(test_user['id'], test_user['email'])


@pytest.fixture(scope='function')
def auth_headers(auth_token):
    """Create authentication headers for API testing"""
    return {'Authorization': f'Bearer {auth_token}'}
