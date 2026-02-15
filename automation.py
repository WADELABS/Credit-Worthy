"""
CredStack Automation Engine
Core logic for calculating statement dates and generating reminders.
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import database

def calculate_next_date(day_of_month, months_ahead=0):
    """Calculate the next occurrence of a specific day of the month"""
    today = datetime.now()
    try:
        target_date = today.replace(day=day_of_month)
    except ValueError:
        # Handle end of month (e.g. 31st)
        target_date = today.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    
    if target_date < today:
        target_date += relativedelta(months=1)
    
    if months_ahead > 0:
        target_date += relativedelta(months=months_ahead)
        
    return target_date

def generate_statement_alert(user_id, account_id, account_name, statement_day):
    """Create a reminder for local statement closing"""
    conn = database.get_db()
    
    # Alert 3 days BEFORE statement closes
    alert_date = calculate_next_date(statement_day) - timedelta(days=3)
    
    message = f"Alert: {account_name} statement closes in 3 days. Pay down balance for low utilization!"
    
    # Check if exists
    exists = conn.execute('''
        SELECT id FROM reminders 
        WHERE user_id = ? AND message LIKE ? AND reminder_date = ?
    ''', (user_id, f"%{account_name}%", alert_date.strftime('%Y-%m-%d'))).fetchone()
    
    if not exists:
        conn.execute('''
            INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
            VALUES (?, ?, ?, ?)
        ''', (user_id, 'automation', alert_date.strftime('%Y-%m-%d'), message))
        conn.commit()
    
    conn.close()

def run_all_automations(user_id):
    """Run all active automations for a user"""
    conn = database.get_db()
    
    # Get user's accounts
    accounts = conn.execute('SELECT * FROM accounts WHERE user_id = ?', (user_id,)).fetchall()
    
    for account in accounts:
        if account['statement_date']:
            generate_statement_alert(user_id, account['id'], account['name'], account['statement_date'])
            
    conn.close()

def create_automated_reminder(user_id, reminder_type, message, days_before=0, reference_date=None):
    """Create an automated reminder"""
    conn = database.get_db()
    
    if reference_date and isinstance(reference_date, int):
        # Handle monthly recurring (like statement dates)
        today = datetime.now()
        try:
            reminder_date = today.replace(day=reference_date) - timedelta(days=days_before)
        except ValueError:
            # End of month
            import calendar
            last_day = calendar.monthrange(today.year, today.month)[1]
            reminder_date = today.replace(day=last_day) - timedelta(days=days_before)
            
        if reminder_date < today:
            from dateutil.relativedelta import relativedelta
            reminder_date += relativedelta(months=1)
        reminder_date_str = reminder_date.strftime('%Y-%m-%d')
    else:
        reminder_date_str = (datetime.now() + timedelta(days=days_before)).strftime('%Y-%m-%d')
    
    conn.execute('''
        INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
        VALUES (?, ?, ?, ?)
    ''', (user_id, reminder_type, reminder_date_str, message))
    conn.commit()
    conn.close()
