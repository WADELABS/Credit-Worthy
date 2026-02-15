#!/usr/bin/env python3
"""
CredStack Background Scheduler
Handles scheduled reminders and automation tasks.
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path to find local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import automation

load_dotenv()

def check_reminders():
    """Check for due reminders and 'send' them"""
    print(f"[{datetime.now()}] Checking for due reminders...")
    
    conn = database.get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get unsent reminders due today or earlier
    reminders = conn.execute('''
        SELECT r.*, u.email, u.phone, u.notification_preference
        FROM reminders r
        JOIN users u ON r.user_id = u.id
        WHERE r.reminder_date <= ? AND r.is_sent = 0
    ''', (today,)).fetchall()
    
    for r in reminders:
        print(f"--- REMINDER DUE: {r['message']} ---")
        print(f"To: {r['email']}")
        print(f"Via: {r['notification_preference']}")
        
        # Mark as sent
        conn.execute('UPDATE reminders SET is_sent = 1 WHERE id = ?', (r['id'],))
        conn.commit()
    
    conn.close()

def generate_recurring_automations():
    """Generate new reminders from active automations"""
    print(f"[{datetime.now()}] Updating automations...")
    
    conn = database.get_db()
    users = conn.execute('SELECT id FROM users').fetchall()
    
    for user in users:
        automation.run_all_automations(user['id'])
    
    conn.close()

def main():
    print("CredStack Scheduler Started...")
    print("Press Ctrl+C to stop.")
    
    # Initial run
    check_reminders()
    generate_recurring_automations()
    
    while True:
        try:
            check_reminders()
            generate_recurring_automations()
            time.sleep(60) # 1 minute for demo purposes
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            break
        except Exception as e:
            print(f"Error in scheduler: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
