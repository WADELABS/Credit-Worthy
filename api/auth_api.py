"""
Authentication API Endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import auth
import database

auth_ns = Namespace('auth', description='Authentication operations')

# Models for request/response
register_model = auth_ns.model('Register', {
    'email': fields.String(required=True, description='User email', example='user@example.com'),
    'password': fields.String(required=True, description='User password (min 8 chars, must contain letter and number)', example='Password123'),
    'name': fields.String(description='User full name', example='John Doe'),
})

login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='User email', example='user@example.com'),
    'password': fields.String(required=True, description='User password', example='Password123'),
})

token_response = auth_ns.model('TokenResponse', {
    'token': fields.String(description='JWT authentication token'),
    'user_id': fields.Integer(description='User ID'),
    'message': fields.String(description='Success message'),
})

error_response = auth_ns.model('Error', {
    'error': fields.String(description='Error message'),
})


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('register_user', 
                 description='Register a new user account',
                 responses={
                     201: ('User created successfully', token_response),
                     400: ('Validation error', error_response),
                 })
    @auth_ns.expect(register_model)
    @auth_ns.marshal_with(token_response, code=201)
    def post(self):
        """Register a new user"""
        data = request.json
        
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        # Validate email
        is_valid, error_msg = auth.validate_email(email)
        if not is_valid:
            auth_ns.abort(400, error_msg)
        
        # Validate password
        is_valid, error_msg = auth.validate_password(password)
        if not is_valid:
            auth_ns.abort(400, error_msg)
        
        # Hash password
        password_hash = auth.hash_password(password)
        
        # Check if user exists
        conn = database.get_db()
        existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            conn.close()
            auth_ns.abort(400, 'Email already registered')
        
        # Create user
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, password_hash, name, notification_preference, automation_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, password_hash, name or None, 'email', 'basic'))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Generate token
        token = auth.create_jwt_token(user_id, email)
        
        return {
            'token': token,
            'user_id': user_id,
            'message': 'User registered successfully'
        }, 201


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login_user',
                 description='Login with email and password to get JWT token',
                 responses={
                     200: ('Login successful', token_response),
                     401: ('Invalid credentials', error_response),
                 })
    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(token_response)
    def post(self):
        """Login and get JWT token"""
        data = request.json
        
        email = data.get('email')
        password = data.get('password')
        
        # Get user
        conn = database.get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if not user:
            conn.close()
            auth_ns.abort(401, 'Invalid email or password')
        
        # Check if account is locked
        is_locked, locked_until = auth.check_account_locked(user)
        if is_locked:
            conn.close()
            auth_ns.abort(401, f'Account locked until {locked_until}')
        
        # Verify password
        if not auth.verify_password(password, user['password_hash']):
            # Increment failed attempts
            failed_attempts = user['failed_login_attempts'] + 1
            
            if failed_attempts >= 3:
                lockout_duration = auth.calculate_lockout_duration(failed_attempts)
                from datetime import datetime, timezone
                locked_until = (datetime.now(timezone.utc) + lockout_duration).isoformat()
                conn.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?, account_locked_until = ?
                    WHERE id = ?
                ''', (failed_attempts, locked_until, user['id']))
            else:
                conn.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?
                    WHERE id = ?
                ''', (failed_attempts, user['id']))
            
            conn.commit()
            conn.close()
            auth_ns.abort(401, 'Invalid email or password')
        
        # Reset failed attempts
        conn.execute('''
            UPDATE users 
            SET failed_login_attempts = 0, account_locked_until = NULL, last_login = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user['id'],))
        conn.commit()
        conn.close()
        
        # Generate token
        token = auth.create_jwt_token(user['id'], email)
        
        return {
            'token': token,
            'user_id': user['id'],
            'message': 'Login successful'
        }


@auth_ns.route('/token/refresh')
class TokenRefresh(Resource):
    @auth_ns.doc('refresh_token',
                 description='Refresh JWT token (requires valid token)',
                 security='Bearer',
                 responses={
                     200: ('Token refreshed', token_response),
                     401: ('Invalid or expired token', error_response),
                 })
    @auth_ns.marshal_with(token_response)
    @auth.token_required
    def post(self):
        """Refresh JWT token"""
        user_id = request.user_id
        
        # Get user email
        conn = database.get_db()
        user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if not user:
            auth_ns.abort(404, 'User not found')
        
        # Generate new token
        token = auth.create_jwt_token(user_id, user['email'])
        
        return {
            'token': token,
            'user_id': user_id,
            'message': 'Token refreshed successfully'
        }
