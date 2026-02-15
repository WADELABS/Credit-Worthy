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
import database
import automation

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-this')

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

@app.route('/login', methods=['POST'])
def login():
    """Simple login (email only for demo)"""
    email = request.form.get('email')
    
    if not email:
        flash('Email is required', 'error')
        return redirect(url_for('index'))
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user:
        # Create user if doesn't exist
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (email, notification_preference, automation_level)
            VALUES (?, ?, ?)
        ''', (email, 'email', 'basic'))
        user_id = cursor.lastrowid
        conn.commit()
    else:
        user_id = user['id']
    
    conn.close()
    
    session['user_id'] = user_id
    session['user_email'] = email
    
    flash(f'Welcome back!', 'success')
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

# Helper functions
create_automated_reminder = automation.create_automated_reminder

if __name__ == '__main__':
    # Ensure database exists
    if not os.path.exists('database/credstack.db'):
        print("Database not found. Running setup...")
        import subprocess
        subprocess.run(['python', 'setup.py'])
    
    app.run(debug=True, port=5000)
