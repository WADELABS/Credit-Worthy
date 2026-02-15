#!/usr/bin/env python3
"""
Authentication Module
Handles password hashing, JWT tokens, and user authentication
"""

import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
import os

# Get secret keys from environment
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-this')
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-this')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Password requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_LETTER = True
REQUIRE_NUMBER = True

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def validate_password(password):
    """
    Validate password meets requirements
    Returns (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    
    if REQUIRE_LETTER and not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    
    if REQUIRE_NUMBER and not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, None

def validate_email(email):
    """
    Basic email validation
    Returns (is_valid, error_message)
    """
    if not email or '@' not in email or '.' not in email:
        return False, "Invalid email format"
    
    if len(email) > 255:
        return False, "Email too long"
    
    return True, None

def generate_api_token():
    """Generate a secure random API token"""
    return secrets.token_urlsafe(32)

def create_jwt_token(user_id, email):
    """Create a JWT token for API authentication"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token):
    """
    Decode and verify a JWT token
    Returns (user_id, email) if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('user_id'), payload.get('email')
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

def token_required(f):
    """Decorator for routes that require JWT token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Check for token in query params (less secure, but convenient)
        if not token and 'token' in request.args:
            token = request.args.get('token')
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        user_id, error = decode_jwt_token(token)
        if not user_id:
            return jsonify({'error': error or 'Invalid token'}), 401
        
        # Add user_id to request context
        request.user_id = user_id
        return f(*args, **kwargs)
    
    return decorated

def check_account_locked(user):
    """
    Check if user account is locked due to failed login attempts
    Returns (is_locked, unlock_time)
    """
    if user['account_locked_until']:
        locked_until = datetime.fromisoformat(user['account_locked_until'])
        if locked_until > datetime.now():
            return True, locked_until
    return False, None

def calculate_lockout_duration(failed_attempts):
    """
    Calculate account lockout duration based on failed attempts
    Returns timedelta
    """
    # Progressive lockout: 5 min, 15 min, 30 min, 1 hour, then 24 hours
    lockout_durations = [
        timedelta(minutes=5),   # 3 failed attempts
        timedelta(minutes=15),  # 4 failed attempts
        timedelta(minutes=30),  # 5 failed attempts
        timedelta(hours=1),     # 6 failed attempts
        timedelta(hours=24)     # 7+ failed attempts
    ]
    
    index = min(failed_attempts - 3, len(lockout_durations) - 1)
    if index < 0:
        return timedelta(0)
    return lockout_durations[index]
