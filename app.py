#!/usr/bin/env python3
"""
CredStack Main Application
Flask web app for credit automation dashboard
"""

import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import database
import automation
import auth

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-this')

# Enable CSRF protection
csrf = CSRFProtect(app)

# Register API blueprint with Swagger documentation
from api import api_bp
app.register_blueprint(api_bp)
# Exempt API routes from CSRF
csrf.exempt(api_bp)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Database helper functions
get_db = database.get_db

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with password"""
    if request.method == 'GET':
        return render_template('register.html')
    
    email = request.form.get('email')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    name = request.form.get('name')
    
    # Validate email
    is_valid, error_msg = auth.validate_email(email)
    if not is_valid:
        flash(error_msg, 'error')
        return redirect(url_for('register'))
    
    # Validate password
    if password != password_confirm:
        flash('Passwords do not match', 'error')
        return redirect(url_for('register'))
    
    is_valid, error_msg = auth.validate_password(password)
    if not is_valid:
        flash(error_msg, 'error')
        return redirect(url_for('register'))
    
    # Hash password
    password_hash = auth.hash_password(password)
    
    # Check if user exists
    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        flash('Email already registered. Please login.', 'error')
        conn.close()
        return redirect(url_for('index'))
    
    # Create user
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, password_hash, name, notification_preference, automation_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, password_hash, name or None, 'email', 'basic'))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Auto-login after registration
    session['user_id'] = user_id
    session['user_email'] = email
    
    flash('Account created successfully! Welcome to CredStack.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Login with email and password"""
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Email and password are required', 'error')
        return redirect(url_for('index'))
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        flash('Invalid email or password', 'error')
        conn.close()
        return redirect(url_for('index'))
    
    # Check if account is locked
    is_locked, unlock_time = auth.check_account_locked(user)
    if is_locked:
        flash(f'Account locked until {unlock_time.strftime("%Y-%m-%d %H:%M")}. Too many failed attempts.', 'error')
        conn.close()
        return redirect(url_for('index'))
    
    # Verify password
    if not user['password_hash']:
        # Legacy user without password - allow migration
        flash('Please set a password for your account', 'warning')
        session['migration_user_id'] = user['id']
        conn.close()
        return redirect(url_for('set_password'))
    
    if not auth.verify_password(password, user['password_hash']):
        # Increment failed attempts
        failed_attempts = user['failed_login_attempts'] + 1
        
        if failed_attempts >= 3:
            lockout_duration = auth.calculate_lockout_duration(failed_attempts)
            locked_until = datetime.now() + lockout_duration
            
            conn.execute('''
                UPDATE users 
                SET failed_login_attempts = ?, account_locked_until = ?
                WHERE id = ?
            ''', (failed_attempts, locked_until.isoformat(), user['id']))
            conn.commit()
            
            flash(f'Too many failed attempts. Account locked for {lockout_duration.seconds // 60} minutes.', 'error')
        else:
            conn.execute('''
                UPDATE users SET failed_login_attempts = ? WHERE id = ?
            ''', (failed_attempts, user['id']))
            conn.commit()
            
            flash('Invalid email or password', 'error')
        
        conn.close()
        return redirect(url_for('index'))
    
    # Reset failed attempts and update last login
    conn.execute('''
        UPDATE users 
        SET failed_login_attempts = 0, account_locked_until = NULL, last_login = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (user['id'],))
    conn.commit()
    conn.close()
    
    session['user_id'] = user['id']
    session['user_email'] = email
    
    flash(f'Welcome back!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/set-password', methods=['GET', 'POST'])
def set_password():
    """Allow users without passwords to set one (migration path)"""
    if 'migration_user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('set_password.html')
    
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')
    
    if password != password_confirm:
        flash('Passwords do not match', 'error')
        return redirect(url_for('set_password'))
    
    is_valid, error_msg = auth.validate_password(password)
    if not is_valid:
        flash(error_msg, 'error')
        return redirect(url_for('set_password'))
    
    password_hash = auth.hash_password(password)
    user_id = session['migration_user_id']
    
    conn = get_db()
    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
    conn.commit()
    
    # Get user email
    user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    # Login user
    session.pop('migration_user_id', None)
    session['user_id'] = user_id
    session['user_email'] = user['email']
    
    flash('Password set successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Log out user"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    conn = get_db()
    user_id = session['user_id']
    
    # Get user info
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Get accounts
    accounts = conn.execute('''
        SELECT * FROM accounts WHERE user_id = ?
        ORDER BY account_type, name
    ''', (user_id,)).fetchall()
    
    # Get automations
    automations = conn.execute('''
        SELECT * FROM automations WHERE user_id = ? AND is_active = 1
        ORDER BY created_at
    ''', (user_id,)).fetchall()
    
    # Get upcoming reminders (next 7 days)
    today = datetime.now().strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    reminders = conn.execute('''
        SELECT * FROM reminders 
        WHERE user_id = ? AND reminder_date BETWEEN ? AND ? AND is_sent = 0
        ORDER BY reminder_date
    ''', (user_id, today, next_week)).fetchall()
    
    # Get active disputes
    disputes = conn.execute('''
        SELECT * FROM disputes 
        WHERE user_id = ? AND status IN ('pending', 'in_progress')
        ORDER BY follow_up_date
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    # Calculate health score (simplified)
    health_score = 750  # Default
    if len(accounts) > 0:
        # Simple scoring based on utilization
        total_balance = sum(a['balance'] for a in accounts if a['balance'])
        total_limit = sum(a['credit_limit'] for a in accounts if a['credit_limit'])
        if total_limit > 0:
            utilization = (total_balance / total_limit) * 100
            if utilization < 10:
                health_score = 780
            elif utilization < 30:
                health_score = 720
            else:
                health_score = 650
    
    return render_template('dashboard.html', 
                          user=user,
                          accounts=accounts,
                          automations=automations,
                          reminders=reminders,
                          disputes=disputes,
                          health_score=health_score,
                          now=datetime.now())

@app.route('/accounts/add', methods=['POST'])
@login_required
def add_account():
    """Add a new account"""
    user_id = session['user_id']
    
    name = request.form.get('name')
    account_type = request.form.get('account_type')
    balance = float(request.form.get('balance', 0))
    credit_limit = float(request.form.get('credit_limit', 0)) if request.form.get('credit_limit') else None
    statement_date = int(request.form.get('statement_date')) if request.form.get('statement_date') else None
    due_date = int(request.form.get('due_date')) if request.form.get('due_date') else None
    min_payment = float(request.form.get('min_payment', 0)) if request.form.get('min_payment') else None
    
    conn = get_db()
    conn.execute('''
        INSERT INTO accounts (user_id, name, account_type, balance, credit_limit, 
                             statement_date, due_date, min_payment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, account_type, balance, credit_limit, 
          statement_date, due_date, min_payment))
    conn.commit()
    conn.close()
    
    # Create statement alert reminder if statement_date provided
    if statement_date:
        automation.generate_statement_alert(user_id, None, name, statement_date)
    
    flash(f'Account "{name}" added successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/accounts/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_account(account_id):
    """Delete an account"""
    user_id = session['user_id']
    
    conn = get_db()
    conn.execute('DELETE FROM accounts WHERE id = ? AND user_id = ?', 
                (account_id, user_id))
    conn.commit()
    conn.close()
    
    flash('Account deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/accounts/<int:account_id>/update-balance', methods=['POST'])
@login_required
def update_balance(account_id):
    """Update account balance"""
    user_id = session['user_id']
    balance = float(request.form.get('balance', 0))
    
    conn = get_db()
    conn.execute('''
        UPDATE accounts SET balance = ?, last_updated = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    ''', (balance, account_id, user_id))
    conn.commit()
    conn.close()
    
    flash('Balance updated', 'success')
    return redirect(url_for('dashboard'))

@app.route('/automations/toggle/<int:auto_id>', methods=['POST'])
@login_required
def toggle_automation(auto_id):
    """Toggle automation on/off"""
    user_id = session['user_id']
    
    conn = get_db()
    current = conn.execute('''
        SELECT is_active FROM automations WHERE id = ? AND user_id = ?
    ''', (auto_id, user_id)).fetchone()
    
    if current:
        new_status = 0 if current['is_active'] else 1
        conn.execute('''
            UPDATE automations SET is_active = ? WHERE id = ? AND user_id = ?
        ''', (new_status, auto_id, user_id))
        conn.commit()
    
    conn.close()
    
    flash('Automation updated', 'success')
    return redirect(url_for('dashboard'))

@app.route('/disputes/add', methods=['POST'])
@login_required
def add_dispute():
    """Add a new dispute"""
    user_id = session['user_id']
    
    bureau = request.form.get('bureau')
    account_name = request.form.get('account_name')
    notes = request.form.get('notes')
    
    dispute_date = datetime.now().strftime('%Y-%m-%d')
    follow_up_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO disputes (user_id, bureau, account_name, dispute_date, follow_up_date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, bureau, account_name, dispute_date, follow_up_date, notes))
    conn.commit()
    conn.close()
    
    flash('Dispute tracked. Follow up on ' + follow_up_date, 'success')
    return redirect(url_for('dashboard'))

@app.route('/disputes/<int:dispute_id>/update', methods=['POST'])
@login_required
def update_dispute(dispute_id):
    """Update dispute status"""
    user_id = session['user_id']
    status = request.form.get('status')
    
    conn = get_db()
    conn.execute('''
        UPDATE disputes SET status = ? WHERE id = ? AND user_id = ?
    ''', (status, dispute_id, user_id))
    conn.commit()
    conn.close()
    
    flash('Dispute updated', 'success')
    return redirect(url_for('dashboard'))

@app.route('/reminders/<int:reminder_id>/complete', methods=['POST'])
@login_required
def complete_reminder(reminder_id):
    """Mark reminder as complete"""
    user_id = session['user_id']
    
    conn = get_db()
    conn.execute('''
        UPDATE reminders SET is_sent = 1 WHERE id = ? AND user_id = ?
    ''', (reminder_id, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/health-score')
@login_required
def api_health_score():
    """API endpoint for health score"""
    user_id = session['user_id']
    
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    
    # Calculate score
    score = 750
    if accounts:
        total_balance = sum(a['balance'] for a in accounts if a['balance'])
        total_limit = sum(a['credit_limit'] for a in accounts if a['credit_limit'] and a['credit_limit'] > 0)
        
        if total_limit > 0:
            utilization = (total_balance / total_limit) * 100
            if utilization < 10:
                score = 780
            elif utilization < 30:
                score = 720
            else:
                score = 650
    
    return jsonify({
        'score': score,
        'date': datetime.now().strftime('%Y-%m-%d')
    })

@app.route('/api/upcoming-reminders')
@login_required
def api_upcoming_reminders():
    """API endpoint for upcoming reminders"""
    user_id = session['user_id']
    
    today = datetime.now().strftime('%Y-%m-%d')
    next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    conn = get_db()
    reminders = conn.execute('''
        SELECT id, reminder_type, reminder_date, message
        FROM reminders 
        WHERE user_id = ? AND reminder_date BETWEEN ? AND ? AND is_sent = 0
        ORDER BY reminder_date
    ''', (user_id, today, next_week)).fetchall()
    conn.close()
    
    return jsonify([dict(r) for r in reminders])

# ==================== API ENDPOINTS ====================
# API Authentication endpoints

@app.route('/api/auth/register', methods=['POST'])
@csrf.exempt  # API endpoints typically don't use CSRF
@limiter.limit("3 per hour")
def api_register():
    """API endpoint for user registration"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    # Validate email
    is_valid, error_msg = auth.validate_email(email)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate password
    is_valid, error_msg = auth.validate_password(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Hash password
    password_hash = auth.hash_password(password)
    
    # Check if user exists
    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    
    # Create user
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, password_hash, name, notification_preference, automation_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, password_hash, name or None, 'email', 'basic'))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Generate JWT token
    token = auth.create_jwt_token(user_id, email)
    
    return jsonify({
        'message': 'Account created successfully',
        'user_id': user_id,
        'token': token
    }), 201

@app.route('/api/auth/login', methods=['POST'])
@csrf.exempt
@limiter.limit("10 per minute")
def api_login():
    """API endpoint for user login"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check if account is locked
    is_locked, unlock_time = auth.check_account_locked(user)
    if is_locked:
        conn.close()
        return jsonify({'error': f'Account locked until {unlock_time.isoformat()}'}), 403
    
    # Verify password
    if not user['password_hash'] or not auth.verify_password(password, user['password_hash']):
        # Increment failed attempts
        failed_attempts = user['failed_login_attempts'] + 1
        
        if failed_attempts >= 3:
            lockout_duration = auth.calculate_lockout_duration(failed_attempts)
            locked_until = datetime.now() + lockout_duration
            
            conn.execute('''
                UPDATE users 
                SET failed_login_attempts = ?, account_locked_until = ?
                WHERE id = ?
            ''', (failed_attempts, locked_until.isoformat(), user['id']))
            conn.commit()
        else:
            conn.execute('''
                UPDATE users SET failed_login_attempts = ? WHERE id = ?
            ''', (failed_attempts, user['id']))
            conn.commit()
        
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Reset failed attempts and update last login
    conn.execute('''
        UPDATE users 
        SET failed_login_attempts = 0, account_locked_until = NULL, last_login = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (user['id'],))
    conn.commit()
    conn.close()
    
    # Generate JWT token
    token = auth.create_jwt_token(user['id'], email)
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user['id'],
        'token': token
    }), 200

@app.route('/api/auth/token/refresh', methods=['POST'])
@auth.token_required
def api_refresh_token():
    """Refresh JWT token"""
    user_id = request.user_id
    
    conn = get_db()
    user = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Generate new token
    token = auth.create_jwt_token(user_id, user['email'])
    
    return jsonify({
        'token': token
    }), 200

@app.route('/api/auth/api-token', methods=['GET', 'POST'])
@auth.token_required
def api_get_api_token():
    """Generate or retrieve API token"""
    user_id = request.user_id
    
    conn = get_db()
    
    if request.method == 'POST':
        # Generate new API token
        api_token = auth.generate_api_token()
        conn.execute('''
            UPDATE users 
            SET api_token = ?, api_token_created = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (api_token, user_id))
        conn.commit()
    else:
        # Retrieve existing token
        user = conn.execute('SELECT api_token FROM users WHERE id = ?', (user_id,)).fetchone()
        api_token = user['api_token']
        
        if not api_token:
            # Generate if doesn't exist
            api_token = auth.generate_api_token()
            conn.execute('''
                UPDATE users 
                SET api_token = ?, api_token_created = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (api_token, user_id))
            conn.commit()
    
    conn.close()
    
    return jsonify({
        'api_token': api_token
    }), 200

# API Credit Data endpoints

@app.route('/api/v1/credit/score', methods=['GET'])
@auth.token_required
def api_v1_credit_score():
    """Get credit health score"""
    user_id = request.user_id
    
    conn = get_db()
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    
    # Calculate score
    score = 750
    utilization = 0
    if accounts:
        total_balance = sum(a['balance'] for a in accounts if a['balance'])
        total_limit = sum(a['credit_limit'] for a in accounts if a['credit_limit'] and a['credit_limit'] > 0)
        
        if total_limit > 0:
            utilization = (total_balance / total_limit) * 100
            if utilization < 10:
                score = 780
            elif utilization < 30:
                score = 720
            else:
                score = 650
    
    return jsonify({
        'score': score,
        'utilization': round(utilization, 2),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'accounts_count': len(accounts)
    }), 200

@app.route('/api/v1/credit/accounts', methods=['GET'])
@auth.token_required
def api_v1_credit_accounts():
    """Get all credit accounts"""
    user_id = request.user_id
    
    conn = get_db()
    accounts = conn.execute('''
        SELECT id, name, account_type, balance, credit_limit, 
               statement_date, due_date, last_updated
        FROM accounts WHERE user_id = ?
        ORDER BY account_type, name
    ''', (user_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(a) for a in accounts]), 200

@app.route('/api/v1/automation/rules', methods=['GET', 'POST'])
@auth.token_required
def api_v1_automation_rules():
    """Get or create automation rules"""
    user_id = request.user_id
    conn = get_db()
    
    if request.method == 'GET':
        automations = conn.execute('''
            SELECT id, automation_type, is_active, configuration, created_at, last_run
            FROM automations WHERE user_id = ?
            ORDER BY created_at
        ''', (user_id,)).fetchall()
        conn.close()
        
        return jsonify([dict(a) for a in automations]), 200
    
    else:  # POST
        data = request.get_json()
        automation_type = data.get('type')
        configuration = data.get('configuration')
        
        if not automation_type:
            conn.close()
            return jsonify({'error': 'Automation type is required'}), 400
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO automations (user_id, automation_type, configuration, is_active)
            VALUES (?, ?, ?, 1)
        ''', (user_id, automation_type, configuration))
        auto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': auto_id,
            'message': 'Automation rule created'
        }), 201

@app.route('/api/v1/disputes', methods=['GET', 'POST'])
@auth.token_required
def api_v1_disputes():
    """Get or create disputes"""
    user_id = request.user_id
    conn = get_db()
    
    if request.method == 'GET':
        status_filter = request.args.get('status')
        query = 'SELECT * FROM disputes WHERE user_id = ?'
        params = [user_id]
        
        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY dispute_date DESC'
        
        disputes = conn.execute(query, params).fetchall()
        conn.close()
        
        return jsonify([dict(d) for d in disputes]), 200
    
    else:  # POST
        data = request.get_json()
        bureau = data.get('bureau')
        creditor = data.get('creditor')
        reason = data.get('reason')
        notes = data.get('notes')
        
        if not bureau or not creditor:
            conn.close()
            return jsonify({'error': 'Bureau and creditor are required'}), 400
        
        dispute_date = datetime.now().strftime('%Y-%m-%d')
        follow_up_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disputes 
            (user_id, bureau, creditor, reason, dispute_date, date_filed, follow_up_date, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, bureau, creditor, reason, dispute_date, dispute_date, follow_up_date, notes))
        dispute_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': dispute_id,
            'message': 'Dispute created',
            'follow_up_date': follow_up_date
        }), 201

@app.route('/api/v1/disputes/<int:dispute_id>', methods=['GET', 'PUT', 'DELETE'])
@auth.token_required
def api_v1_dispute_detail(dispute_id):
    """Get, update, or delete a specific dispute"""
    user_id = request.user_id
    conn = get_db()
    
    # Verify ownership
    dispute = conn.execute('''
        SELECT * FROM disputes WHERE id = ? AND user_id = ?
    ''', (dispute_id, user_id)).fetchone()
    
    if not dispute:
        conn.close()
        return jsonify({'error': 'Dispute not found'}), 404
    
    if request.method == 'GET':
        conn.close()
        return jsonify(dict(dispute)), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        status = data.get('status')
        outcome = data.get('outcome')
        notes = data.get('notes')
        
        updates = []
        params = []
        
        if status:
            updates.append('status = ?')
            params.append(status)
            
            if status in ['resolved', 'rejected']:
                updates.append('date_resolved = ?')
                params.append(datetime.now().strftime('%Y-%m-%d'))
        
        if outcome:
            updates.append('outcome = ?')
            params.append(outcome)
        
        if notes is not None:
            updates.append('notes = ?')
            params.append(notes)
        
        if updates:
            params.extend([dispute_id, user_id])
            conn.execute(f'''
                UPDATE disputes SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
            ''', params)
            conn.commit()
        
        conn.close()
        return jsonify({'message': 'Dispute updated'}), 200
    
    else:  # DELETE
        conn.execute('DELETE FROM disputes WHERE id = ? AND user_id = ?', (dispute_id, user_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Dispute deleted'}), 200

@app.route('/api/v1/user/profile', methods=['GET', 'PUT'])
@auth.token_required
def api_v1_user_profile():
    """Get or update user profile"""
    user_id = request.user_id
    conn = get_db()
    
    if request.method == 'GET':
        user = conn.execute('''
            SELECT id, email, name, phone, notification_preference, 
                   automation_level, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(dict(user)), 200
    
    else:  # PUT
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        notification_preference = data.get('notification_preference')
        
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        
        if phone is not None:
            updates.append('phone = ?')
            params.append(phone)
        
        if notification_preference:
            updates.append('notification_preference = ?')
            params.append(notification_preference)
        
        if updates:
            params.append(user_id)
            conn.execute(f'''
                UPDATE users SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            conn.commit()
        
        conn.close()
        return jsonify({'message': 'Profile updated'}), 200

# Helper functions
create_automated_reminder = automation.create_automated_reminder

if __name__ == '__main__':
    # Ensure database exists
    if not os.path.exists('database/credstack.db'):
        print("Database not found. Running setup...")
        import subprocess
        subprocess.run(['python', 'setup.py'])
    
    app.run(debug=True, port=5000)
